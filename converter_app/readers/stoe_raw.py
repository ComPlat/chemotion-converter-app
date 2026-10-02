import logging
import struct
from collections import namedtuple

import numpy as np

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

# The file is organised in blocks of 512 bytes.
BLOCK_SIZE = 0x200

# Absolute offsets in the primary header.
OFF_DATE = 0x0010            # 16 bytes ASCII, "dd-Mon-yy hh:mm"
OFF_STRINGS = 0x0020         # NUL separated ASCII strings: sample id, title, comments
OFF_STRINGS_END = 0x0130
OFF_WAVELENGTH = 0x0142      # 2 x float32: K-alpha1, K-alpha2 / Angstrom
OFF_NPOINTS_PLUS1 = 0x01D2   # uint16, number of points + 1 (cross-check only)
OFF_DATA_BLOCKS = 0x01DA     # uint16, length of the intensity block in blocks
OFF_TOTAL_BLOCKS = 0x01DC    # uint16, file length in blocks
OFF_OPERATOR = 0x0600        # NUL terminated ASCII
OPERATOR_LEN = 0x20

# Offsets relative to the start of the intensity block. The range header
# occupies the block directly in front of it.
REL_T_START = -0x200         # 16 bytes ASCII, "dd-Mon-yy hh:mm"
REL_T_END = -0x1F0           # 16 bytes ASCII, "dd-Mon-yy hh:mm"
REL_NPOINTS = -0x1DE         # uint16
REL_SCAN = -0x1D4            # 6 x float32: start 2theta, start theta, end 2theta, end theta, step 2theta, step theta
REL_IMIN = -0x188            # uint32
REL_IMAX = -0x184            # uint32

ScanRange = namedtuple('ScanRange', 'offset source n_points scan i_min i_max intensities')


class StoeRawReader(Reader):
    """
    Reader for STOE raw powder diffraction files ("RAW_1.06Powdat").

    Code was extracted from the TVB jupyter notebook
    "Simple Conversion of Stoe raw data file"
    by Ron Dockhorn (https://orcid.org/0000-0002-5268-5430).

    Revised by DELFIN and Claude Agent to make the offsets robust and flexible:
    the notebook used fixed offsets that only fit files with a 256 kB primary
    header. The start of the intensity block is now derived from the block
    counters in the header, and all scan fields are read relative to it. If the
    counters do not lead to a valid scan range, every block boundary is tried.
    A scan range is only accepted if its point count matches the scan
    parameters and its intensities match the header intensity range, so
    compact and padded file variants are read alike, and an unknown layout
    raises an error instead of returning wrong data.

    Layout (little endian):

        0x0000  magic "RAW_1.06Powdat"
        0x0010  measurement date, ASCII
        0x0020  NUL separated strings (sample id, title, comments)
        0x0142  K-alpha1, K-alpha2 wavelength (float32, Angstrom)
        0x01DA  length of the intensity block in 512-byte blocks (uint16)
        0x01DC  file length in 512-byte blocks (uint16)
        0x0600  operator (ASCII)

        D = (blocks@0x01DC - blocks@0x01DA) * 512, start of the intensity block
        D-0x200 scan start time, ASCII
        D-0x1F0 scan end time, ASCII
        D-0x1DE number of points (uint16)
        D-0x1D4 start/end/step of 2theta and theta (6 x float32, deg)
        D-0x188 min/max intensity (2 x uint32)
        D       intensities (uint32 per point)

    Only files with a single scan range are supported.
    """
    identifier = 'stoe_raw_reader'
    priority = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_type = None

    def check(self):
        """
        :return: True if it fits
        """

        return (
                self.file.suffix.lower() == ".raw"
                and self.file.encoding.lower() == "binary"
                and self.file_type == "RAW_1.06Powdat"
        )

    @property
    def file_type(self):
        """
        :return: The magic string at the start of the file
        """
        if self._file_type is None:
            self._file_type = self.file.content[0x00:0x0E].decode('latin-1')
        return self._file_type

    def prepare_tables(self):
        content = self.file.content
        if len(content) < 2 * BLOCK_SIZE:
            raise ValueError(f'STOE raw file {self.file.name} is truncated ({len(content)} bytes)')

        tables = []
        table = self.append_table(tables)

        table['metadata']['File Type'] = self.file_type

        date, time = self._split_date_time(self._read_ascii(OFF_DATE, 16))
        table['metadata']['Ex date'] = date
        table['metadata']['Ex time'] = time

        strings = self._read_strings()
        table['header'] += strings

        alpha1, alpha2 = struct.unpack_from('<2f', content, OFF_WAVELENGTH)
        table['metadata']['Alpha1 x-ray wavelength'] = str(alpha1)

        scan_range = self._find_scan_range()

        for key, offset in (('Start', REL_T_START), ('End', REL_T_END)):
            date, time = self._split_date_time(self._read_ascii(scan_range.offset + offset, 16))
            if date:
                table['metadata'][f'{key} date'] = date
                table['metadata'][f'{key} time'] = time

        table['metadata']['Data entries'] = str(scan_range.n_points)

        table['metadata']['SampleId'] = strings[0] if strings else ''
        table['metadata']['Operator'] = self._read_ascii(OFF_OPERATOR, OPERATOR_LEN)
        table['metadata']['WavelengthAlpha2_Å'] = self._format_float(alpha2)
        self._add_scan_metadata(table, scan_range)

        start_2theta, end_2theta = scan_range.scan[0], scan_range.scan[2]
        x_range = np.linspace(start_2theta, end_2theta, scan_range.n_points, True)
        table['rows'] = [[float(x), int(y)] for x, y in zip(x_range, scan_range.intensities)]

        return tables

    def _add_scan_metadata(self, table, scan_range: ScanRange):
        start_2theta, start_theta, end_2theta, end_theta, step_2theta, step_theta = scan_range.scan
        table['metadata']['TwoThetaStart_°'] = self._format_float(start_2theta)
        table['metadata']['TwoThetaEnd_°'] = self._format_float(end_2theta)
        table['metadata']['TwoThetaStep_°'] = self._format_float(step_2theta)
        table['metadata']['ThetaStart_°'] = self._format_float(start_theta)
        table['metadata']['ThetaEnd_°'] = self._format_float(end_theta)
        table['metadata']['ThetaStep_°'] = self._format_float(step_theta)
        table['metadata']['IntensityMin_counts'] = str(scan_range.i_min)
        table['metadata']['IntensityMax_counts'] = str(scan_range.i_max)
        table['metadata']['DataOffset_bytes'] = str(scan_range.offset)
        table['metadata']['DataOffsetSource'] = scan_range.source

    def _find_scan_range(self) -> ScanRange:
        content = self.file.content
        total_blocks = struct.unpack_from('<H', content, OFF_TOTAL_BLOCKS)[0]
        data_blocks = struct.unpack_from('<H', content, OFF_DATA_BLOCKS)[0]

        candidates = []
        if 0 < data_blocks < total_blocks:
            candidates.append(((total_blocks - data_blocks) * BLOCK_SIZE, 'header block count'))
        # Fallback: the intensity block always starts on a block boundary.
        candidates += [(offset, 'block search') for offset in range(BLOCK_SIZE, len(content), BLOCK_SIZE)]

        for offset, source in candidates:
            scan_range = self._read_scan_range(offset, source)
            if scan_range is not None:
                if source != 'header block count':
                    logger.warning('STOE raw file %s: block counters (%d, %d) do not point to the scan range, '
                                   'found it at offset %d by block search',
                                   self.file.name, total_blocks, data_blocks, offset)
                n_hint = struct.unpack_from('<H', content, OFF_NPOINTS_PLUS1)[0]
                if n_hint - 1 != scan_range.n_points:
                    logger.warning('STOE raw file %s: header point counter (%d) does not match the scan range (%d)',
                                   self.file.name, n_hint - 1, scan_range.n_points)
                return scan_range

        raise ValueError(f'No valid scan range found in STOE raw file {self.file.name}')

    def _read_scan_range(self, offset: int, source: str) -> ScanRange | None:
        """
        Reads the scan range whose intensity block starts at offset.
        :return: ScanRange, or None if the data at offset is not a consistent scan range
        """
        content = self.file.content
        if offset < BLOCK_SIZE or offset > len(content):
            return None

        n_points = struct.unpack_from('<H', content, offset + REL_NPOINTS)[0]
        if n_points == 0 or offset + 4 * n_points > len(content):
            return None

        scan = struct.unpack_from('<6f', content, offset + REL_SCAN)
        start, end, step = scan[0], scan[2], scan[4]
        if not (np.isfinite([start, end, step]).all() and step > 0 and end > start):
            return None
        if abs(round((end - start) / step) + 1 - n_points) > 1:
            return None

        i_min, i_max = struct.unpack_from('<2I', content, offset + REL_IMIN)
        intensities = np.frombuffer(content, dtype='<u4', count=n_points, offset=offset)
        # A zero max means the header range is not set, so nothing to compare.
        if i_max and (int(intensities.min()) != i_min or int(intensities.max()) != i_max):
            return None

        return ScanRange(offset, source, n_points, scan, i_min, i_max, intensities)

    def _read_ascii(self, offset: int, length: int) -> str:
        """
        Reads a NUL terminated ASCII field.
        """
        raw = self.file.content[offset:offset + length]
        return raw.split(b'\x00', 1)[0].decode('latin-1').strip()

    def _read_strings(self) -> list[str]:
        """
        Reads all NUL separated strings of the primary header, one entry per line.
        """
        data = self.file.content[OFF_STRINGS:OFF_STRINGS_END]
        lines = []
        for chunk in data.split(b'\x00'):
            for line in chunk.decode('latin-1').split('\n'):
                if line.strip():
                    lines.append(line.strip())
        return lines

    @staticmethod
    def _split_date_time(value: str) -> tuple[str, str]:
        parts = value.split()
        return (parts[0] if parts else ''), (parts[1] if len(parts) > 1 else '')

    @staticmethod
    def _format_float(value: float) -> str:
        # float32 holds about 7 significant digits
        return f'{value:.7g}'


Readers.instance().register(StoeRawReader)
