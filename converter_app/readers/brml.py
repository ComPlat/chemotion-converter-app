import logging
import zipfile
from collections import namedtuple

import defusedxml.ElementTree as ET

from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)

# Declarative description of a single metadata field to extract.
#
#   path   -- '/'-separated local-name path to the element, relative to the base
#             node the field is applied to. An empty string means the base node
#             itself.
#   kind   -- how the value is read from that element:
#               'attr'       -> element.get(source); ``source`` may be a tuple of
#                               attribute names, the first non-empty one wins.
#               'text'       -> element.text (stripped).
#               'value_unit' -> element.get('Value'), with element.get('Unit')
#                               appended to ``key`` as a '_<unit>' suffix.
#   source -- attribute name(s) for kind 'attr'; ignored otherwise.
#   key    -- the metadata key written to the output table.
_Field = namedtuple('_Field', 'path kind source key')


class BrmlReader(Reader):
    """
    Reader for Bruker BRML files (powder diffraction, e.g. D8 Advance / DaVinci).

    A BRML file is a ZIP archive holding one or more ``ExperimentN`` folders. Each
    experiment has a ``DataContainer.xml`` (sample and instrument level information)
    that references one or more ``RawDataN.xml`` files (scan setup and the measured
    data points).

    For every ``DataRoute`` found in the referenced raw data one table is produced:

    * ``rows``    -- the measured data points (one row per ``Datum``), plus a derived
                     ``Intensity_cps`` column (counts / measured time).
    * ``columns`` -- named according to the ``DataView`` definition, e.g.
                     ``MeasuredTime_s``, ``AbsorptionFactor``, ``2Theta_°``,
                     ``Theta_°``, ``ScanCounter_Counts``.
    * ``metadata`` -- the most relevant sample, instrument, source and scan
                      parameters. Values carry their physical unit as a ``_<unit>``
                      suffix where one is available (e.g. ``Voltage_kV``).

    Which metadata is extracted is defined declaratively in the ``*_FIELDS`` tables
    below (element path -> output key), so extending the output is a one-line change
    rather than new extraction logic.

    Only ``DataContainer.xml`` and the referenced ``RawDataN.xml`` files are parsed.
    Additional optics details (individual slits, Soller collimators, goniometer
    radius, temperature, sample rotation, ...) live in the much larger
    ``MeasurementContainer.xml`` and are intentionally not read here, to keep the
    reader fast and robust. They could be added later as an optional "deep"
    extraction step if required.

    The XML traversal is namespace tolerant: elements are matched by their local
    name, so both plain and namespace-qualified BRML variants are supported.
    """

    identifier = 'brml_reader'
    priority = 10

    # Sample and instrument level fields, relative to the DataContainer.xml root.
    CONTAINER_FIELDS = (
        _Field('CreatingVersion', 'text', None, 'Software version'),
        _Field('Identifier/TimeStampCreated', 'text', None, 'Timestamp created'),
        _Field('MeasurementInfo', 'attr', 'SampleName', 'Sample name'),
        _Field('MeasurementInfo', 'attr', 'UserName', 'Operator'),
        _Field('MeasurementInfo', 'attr', 'Comment', 'Comment'),
        _Field('MeasurementInfo', 'attr', 'SamplePosition', 'Sample position'),
        _Field('MeasurementInfo', 'attr', ('BsmlFileName', 'ScriptName'), 'Script file'),
        _Field('ExperimentInfo/InstrumentDescription/InstrumentName', 'text', None, 'Instrument'),
        _Field('ExperimentInfo/InstrumentDescription/SerialNo', 'text', None, 'Serial number'),
        _Field('ExperimentInfo/InstrumentDescription/DeviceTypeDesc', 'text', None, 'Device type'),
        _Field('ExperimentInfo/ApplicationType', 'text', None, 'Application type'),
        _Field('TotalMeasurementTime', 'value_unit', None, 'TotalMeasurementTime'),
    )

    # Status fields, relative to the RawDataN.xml root.
    RAW_FIELDS = (
        _Field('MeasurementStatus', 'text', None, 'Measurement status'),
        _Field('TimeStampStarted', 'text', None, 'Timestamp started'),
        _Field('TimeStampFinished', 'text', None, 'Timestamp finished'),
    )

    # Fields relative to a single DataRoute element.
    ROUTE_FIELDS = (
        _Field('', 'attr', 'Description', 'Data route'),
        _Field('', 'attr', 'RouteFlag', 'Route flag'),
    )

    # Fields relative to a ScanInformation element.
    SCAN_FIELDS = (
        _Field('', 'attr', ('VisibleName', 'ScanName'), 'Scan name'),
        _Field('MeasurementPoints', 'text', None, 'Measurement points'),
        _Field('TimePerStep', 'text', None, 'TimePerStep_s'),
        _Field('TimePerStepEffective', 'text', None, 'TimePerStepEffective_s'),
        _Field('EstimatedTime', 'text', None, 'EstimatedTime_s'),
        _Field('ScanMode', 'text', None, 'Scan mode'),
        _Field('ScanModeVisibleName', 'text', None, 'Scan mode description'),
    )

    # X-ray source fields, relative to the Tube element.
    TUBE_FIELDS = (
        _Field('', 'attr', 'LogicName', 'Tube'),
        _Field('WaveLengthAlpha1', 'value_unit', None, 'WaveLengthAlpha1'),
        _Field('WaveLengthAlpha2', 'value_unit', None, 'WaveLengthAlpha2'),
        _Field('WaveLengthAverage', 'value_unit', None, 'WaveLengthAverage'),
        _Field('WaveLengthBeta', 'value_unit', None, 'WaveLengthBeta'),
        _Field('WaveLengthRatio', 'value_unit', None, 'WaveLengthRatio'),
        _Field('Generator/Voltage', 'value_unit', None, 'Voltage'),
        _Field('Generator/Current', 'value_unit', None, 'Current'),
    )

    # Sealed-tube anode materials, used to derive the anode from the tube name.
    # Two-letter symbols first so they win over the single-letter tungsten symbol.
    ANODE_MATERIALS = ('Ag', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'Mo', 'Ni', 'Rh', 'W')

    def check(self):
        """
        :return: True if the file is a BRML (ZIP) archive
        """
        if self.file.suffix.lower() != '.brml':
            return False
        try:
            is_zip = zipfile.is_zipfile(self.file.fp)
        finally:
            self.file.fp.seek(0)
        return is_zip

    # -- XML helpers (namespace tolerant) ---------------------------------------

    @staticmethod
    def _local_name(elem) -> str:
        """Return the tag of ``elem`` without any XML namespace prefix."""
        return elem.tag.rsplit('}', 1)[-1]

    @classmethod
    def _children(cls, node, name) -> list:
        """All direct children of ``node`` whose local name equals ``name``."""
        if node is None:
            return []
        return [child for child in list(node) if cls._local_name(child) == name]

    @classmethod
    def _child(cls, node, name):
        """First direct child of ``node`` whose local name equals ``name`` (or None)."""
        for child in cls._children(node, name):
            return child
        return None

    @classmethod
    def _path(cls, node, path):
        """First element reached by descending a '/'-separated path of local names."""
        current = node
        for part in path.split('/'):
            current = cls._child(current, part)
            if current is None:
                return None
        return current

    @classmethod
    def _path_all(cls, node, path) -> list:
        """All elements reached by descending a '/'-separated path of local names."""
        current = [node]
        for part in path.split('/'):
            nxt = []
            for element in current:
                nxt.extend(cls._children(element, part))
            current = nxt
        return current

    @classmethod
    def _find_first(cls, node, name):
        """First descendant (any depth, including ``node``) with local name ``name``."""
        if node is None:
            return None
        for element in node.iter():
            if cls._local_name(element) == name:
                return element
        return None

    @classmethod
    def _text(cls, node, path, default='') -> str:
        """Stripped text of the element at ``path`` below ``node`` (or ``default``)."""
        element = cls._path(node, path) if path else node
        if element is None or element.text is None:
            return default
        return element.text.strip()

    @staticmethod
    def _key(name, unit) -> str:
        """Build a metadata/column key, appending the unit as ``_<unit>`` if present."""
        unit = (unit or '').strip()
        return f'{name}_{unit}' if unit else name

    @staticmethod
    def _basename(path) -> str:
        return path.rsplit('/', 1)[-1]

    # -- main entry point -------------------------------------------------------

    def prepare_tables(self):
        tables = []
        with zipfile.ZipFile(self.file.fp) as zf:
            names = zf.namelist()
            data_container_names = sorted(
                name for name in names if self._basename(name) == 'DataContainer.xml'
            )
            if not data_container_names:
                logger.warning('BRML %s: no DataContainer.xml found', self.file.name)

            for dc_name in data_container_names:
                try:
                    self._process_data_container(zf, dc_name, names, tables)
                except Exception as exc:  # keep the remaining experiments alive
                    logger.warning('BRML %s: failed to process %s: %s',
                                   self.file.name, dc_name, exc)
        return tables

    def _process_data_container(self, zf, dc_name, names, tables):
        with zf.open(dc_name) as fp:
            dc_root = ET.fromstring(fp.read())

        refs = [s.text for s in self._path_all(dc_root, 'RawDataReferenceList/string')
                if s.text]
        if not refs:
            # Fallback: any RawData*.xml sibling inside the same experiment folder.
            prefix = dc_name[:-len('DataContainer.xml')]
            refs = sorted(
                name for name in names
                if name.startswith(prefix) and self._basename(name).startswith('RawData')
            )

        for ref in refs:
            if ref not in names:
                logger.warning('BRML %s: referenced raw data "%s" not found',
                               self.file.name, ref)
                continue
            with zf.open(ref) as fp:
                raw_root = ET.fromstring(fp.read())
            self._process_raw_data(dc_root, raw_root, tables)

    def _process_raw_data(self, dc_root, raw_root, tables):
        for data_route in self._path_all(raw_root, 'DataRoutes/DataRoute'):
            table = self.append_table(tables)

            self._extract_fields(table, dc_root, self.CONTAINER_FIELDS)
            self._extract_fields(table, raw_root, self.RAW_FIELDS)
            self._extract_fields(table, data_route, self.ROUTE_FIELDS)

            scan = self._path(data_route, 'ScanInformation')
            if scan is not None:
                self._extract_fields(table, scan, self.SCAN_FIELDS)
                for axis in self._path_all(scan, 'ScanAxes/ScanAxisInfo'):
                    self._add_axis_metadata(table, axis)
                for axis in self._path_all(scan, 'FixedScanAxes/FixedScanAxisInfo'):
                    self._add_fixed_axis_metadata(table, axis)

            self._add_source_metadata(table, data_route, raw_root)
            self._add_detector_metadata(table, data_route)

            columns = self._column_definitions(data_route)
            # Add a derived counts-per-second column when both the measured time and
            # the counter column are known. This mirrors the cps values found in the
            # ASCII (.xy) export while keeping the raw counts untouched.
            time_index, counts_index = self._intensity_source_indices(columns)
            add_cps = time_index is not None and counts_index is not None
            if add_cps:
                columns = columns + [('Intensity', 'cps')]
            self._apply_columns(table, columns)

            for datum in self._path_all(data_route, 'Datum'):
                if datum.text is None:
                    continue
                text = datum.text.strip()
                if not text:
                    continue
                row = [value.strip() for value in text.split(',')]
                if add_cps:
                    row.append(self._compute_cps(row, time_index, counts_index))
                table['rows'].append(row)

    # -- metadata extraction ----------------------------------------------------

    def _extract_fields(self, table, node, fields):
        """Extract every field of a declarative ``*_FIELDS`` table from ``node``."""
        for field in fields:
            element = self._path(node, field.path) if field.path else node
            if element is None:
                continue
            if field.kind == 'attr':
                sources = field.source if isinstance(field.source, tuple) else (field.source,)
                for attr in sources:
                    value = element.get(attr, '')
                    if value:
                        self._add(table, field.key, value)
                        break
            elif field.kind == 'text':
                self._add(table, field.key, (element.text or '').strip())
            elif field.kind == 'value_unit':
                self._add(table, self._key(field.key, element.get('Unit', '')),
                          element.get('Value', ''))

    def _add_axis_metadata(self, table, axis):
        """Start/Stop/Increment of a moving scan axis (e.g. TwoTheta, Theta)."""
        name = (axis.get('VisibleName') or axis.get('AxisName')
                or axis.get('AxisId') or 'Axis')
        unit = axis.get('Unit', '')
        for tag in ('Start', 'Stop', 'Increment'):
            self._add(table, self._key(f'{name}{tag}', unit), self._text(axis, tag))

    def _add_fixed_axis_metadata(self, table, axis):
        """Fixed position of a non-moving axis (e.g. PSD opening)."""
        name = (axis.get('VisibleName') or axis.get('AxisName')
                or axis.get('AxisId') or 'FixedAxis')
        unit = axis.get('Unit', '')
        self._add(table, self._key(name, unit), self._text(axis, 'Position'))

    def _add_source_metadata(self, table, *nodes):
        """X-ray source: tube, wavelengths, generator settings and anode material."""
        tube = None
        for node in nodes:
            tube = self._find_first(node, 'Tube')
            if tube is not None:
                break
        if tube is None:
            return
        self._extract_fields(table, tube, self.TUBE_FIELDS)
        # The anode material is not stored explicitly; derive it from the tube name.
        self._add(table, 'Anode', self._derive_anode(tube.get('LogicName')))

    def _add_detector_metadata(self, table, data_route):
        """Detector name, taken from the counter's DataView ``Recording`` element."""
        recording = self._find_first(data_route, 'Recording')
        if recording is not None:
            self._add(table, 'Detector',
                      recording.get('ParentBeringObjectName')
                      or recording.get('VisibleName'))

    @classmethod
    def _derive_anode(cls, tube_name):
        """Heuristically derive the anode material from the tube name (e.g. Cu)."""
        if not tube_name:
            return ''
        for symbol in cls.ANODE_MATERIALS:
            if symbol in tube_name:
                return symbol
        return ''

    @staticmethod
    def _add(table, key, value):
        """Add ``value`` to the table metadata only if it is a non-empty string."""
        if value:
            table.add_metadata(key, value)

    # -- column definitions -----------------------------------------------------

    def _column_definitions(self, data_route) -> list:
        """
        Derive ordered ``(name, unit)`` column definitions from the ``DataView``.

        The views are ordered by their ``Start`` index so that the resulting columns
        line up with the comma separated values of each ``Datum``. If no ``DataView``
        is present an empty list is returned and the base reader falls back to
        generic ``Column #n`` names.
        """
        views = self._path(data_route, 'DataViews')
        if views is None:
            return []

        entries = []
        for view in list(views):
            if self._local_name(view) != 'RawDataView':
                continue
            try:
                start = int(view.get('Start', '0'))
            except (TypeError, ValueError):
                start = 0
            entries.append((start, self._view_columns(view)))

        entries.sort(key=lambda entry: entry[0])
        columns = []
        for _start, view_columns in entries:
            columns.extend(view_columns)
        return columns

    def _view_columns(self, view) -> list:
        """Return the ``(name, unit)`` columns contributed by a single ``RawDataView``."""
        varying = self._child(view, 'Varying')
        recording = self._child(view, 'Recording')

        if varying is not None:
            columns = []
            for field in self._children(varying, 'FieldDefinitions'):
                name = self._text(field, 'VisibleName') or field.get('FieldName') or 'Value'
                restriction = self._child(field, 'Restriction')
                unit = restriction.get('Unit', '') if restriction is not None else ''
                columns.append((name, unit))
            return columns

        if recording is not None:
            name = (recording.get('LogicName')
                    or self._text(recording, 'VisibleName') or 'Value')
            unit_element = self._child(recording, 'Unit')
            unit = unit_element.get('Base', '') if unit_element is not None else ''
            return [(name, unit)]

        # FixedRawDataView: a single scalar column with LogicName and Unit attributes.
        return [(view.get('LogicName') or 'Value', view.get('Unit', ''))]

    def _apply_columns(self, table, columns):
        table['columns'] = [
            {'key': str(index), 'name': self._key(name, unit)}
            for index, (name, unit) in enumerate(columns)
        ]

    # -- derived counts-per-second column ---------------------------------------

    @staticmethod
    def _intensity_source_indices(columns):
        """
        Locate the measured-time and counter columns by meaning (not by position).

        :param columns: ordered list of ``(name, unit)`` column definitions
        :return: ``(time_index, counts_index)``; either may be None if not found
        """
        time_index = counts_index = None
        for index, (name, unit) in enumerate(columns):
            if name == 'MeasuredTime' and time_index is None:
                time_index = index
            if counts_index is None and (name == 'ScanCounter'
                                         or (unit or '').strip().lower() == 'counts'):
                counts_index = index
        return time_index, counts_index

    @staticmethod
    def _compute_cps(row, time_index, counts_index):
        """
        Counts per second for a single data point: ``counts / measured_time``.

        The result keeps full precision (no rounding); ``str`` yields the shortest
        decimal that round-trips to the exact quotient. Returns an empty string when
        the value cannot be computed.
        """
        try:
            counts = float(row[counts_index])
            seconds = float(row[time_index])
        except (ValueError, IndexError):
            return ''
        if seconds == 0:
            return ''
        return str(counts / seconds)


Readers.instance().register(BrmlReader)
