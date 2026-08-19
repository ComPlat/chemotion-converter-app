import io
import logging
import re
import struct

import olefile

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class JwsReader(Reader):
    """
    Reads native JASCO Spectra Manager files (.jws), an OLE2 compound document.

    A single .jws holds one spectrum. The relevant streams are:
      - 'DataInfo': doubles; index 3/4/5 = X start / end / interval (nm)
      - 'Y-Data'  : N little-endian float32 intensities
      - 'X-Data'  : present only for non-linear arrays (then X is read from here)
      - 'SampleInfo' / 'ModuleInfo' / 'MeasParam' / 'UserInfo': UTF-16LE text metadata

    Emits a single table (Wavelength vs Intensity) plus metadata. Column names and the
    internal_reader_* keys mirror the SuprabankReader spectra pages so the data is comparable.

    Note: the binary layout is reverse-engineered and verified against FP-8300 emission
    spectra. Files with a differing data-array type are rejected in check() rather than
    guessed at.
    """
    identifier = 'jws_reader'
    priority = 10

    # DataInfo layout: X start / end / interval are the doubles at index 3, 4, 5
    _DATAINFO_XAXIS_OFFSET = 3 * 8
    # token pattern for a measured parameter like '2.5 nm' or '1 sec'
    _param_pattern = re.compile(r'^\d+(?:\.\d+)?\s*(?:nm|sec|s)$')

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self._ole = None

    @staticmethod
    def _open_jws(content):
        """Open and validate a .jws OLE2 blob. Returns the OleFileIO, or None if it is not a .jws."""
        try:
            ole = olefile.OleFileIO(io.BytesIO(content))
        except (OSError, ValueError):
            return None
        streams = {'/'.join(entry) for entry in ole.listdir()}
        if 'DataInfo' in streams and 'Y-Data' in streams:
            return ole
        ole.close()
        return None

    def check(self):
        """
        :return: True if the file is a readable JASCO .jws OLE2 file with the expected streams
        """
        if self.file.suffix.lower() != '.jws' or self.file.encoding.lower() != 'binary':
            return False

        ole = self._open_jws(self.file.content)
        result = ole is not None
        if result:
            self._ole = ole

        logger.debug('result=%s', result)
        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        self._populate_spectrum(self._ole, table)
        return tables

    def _populate_spectrum(self, ole, table):
        """Fill one table (columns/rows + device metadata) from an opened .jws OLE2 file."""
        # X axis: start / end / interval from DataInfo
        data_info = ole.openstream('DataInfo').read()
        x_start, x_end, x_step = struct.unpack_from('<3d', data_info, self._DATAINFO_XAXIS_OFFSET)

        # Y values: N little-endian float32
        y_raw = ole.openstream('Y-Data').read()
        n_points = len(y_raw) // 4
        y_values = struct.unpack(f'<{n_points}f', y_raw[:n_points * 4])

        # X values: read from 'X-Data' for non-linear arrays, otherwise reconstruct linearly
        if ole.exists('X-Data'):
            x_raw = ole.openstream('X-Data').read()
            x_values = struct.unpack(f'<{n_points}f', x_raw[:n_points * 4])
        else:
            x_values = [x_start + i * x_step for i in range(n_points)]

        table['rows'] = [[x, y] for x, y in zip(x_values, y_values)]
        table['columns'] = [
            {'key': '0', 'name': 'Wavelength [nm]'},
            {'key': '1', 'name': 'Intensity [a.u.]'},
        ]

        # metadata
        meta = table['metadata']
        meta['internal_reader_name'] = 'jasco'
        meta['internal_reader_type'] = 'fluorescence spectrum'
        meta['Start'] = f'{x_start:g} nm'
        meta['End'] = f'{x_end:g} nm'
        meta['Data interval'] = f'{x_step:g} nm'
        meta['Data points'] = str(n_points)

        self._add_text_metadata(meta, ole)

    def _add_text_metadata(self, meta, ole):
        """Best-effort extraction of the UTF-16LE text streams (fields carry binary separators)."""
        sample = self._tokens(ole, 'SampleInfo')
        if sample:
            meta['Sample name'] = max(sample, key=len)

        user = self._tokens(ole, 'UserInfo')
        if user:
            meta['User'] = max(user, key=len)

        # ModuleInfo carries model / serial / accessory / accessory S/N in this order
        module = self._tokens(ole, 'ModuleInfo')
        for key, value in zip(['Model name', 'Serial No.', 'Accessory', 'Accessory S/N'], module):
            meta[key] = value

        # MeasParam: keep the recognizable measured parameters (e.g. '2.5 nm', '1 sec')
        params = [tok for tok in self._tokens(ole, 'MeasParam') if self._param_pattern.match(tok)]
        for idx, value in enumerate(params):
            meta[f'MeasParam_{idx:02d}'] = value

    @staticmethod
    def _tokens(ole, stream):
        """Returns the ASCII-printable UTF-16LE tokens (>= 2 chars) of a stream, dropping binary noise."""
        if not ole.exists(stream):
            return []
        text = ole.openstream(stream).read().decode('utf-16-le', errors='ignore')
        tokens = []
        for token in text.split('\x00'):
            token = token.strip()
            if len(token) >= 2 and all(32 <= ord(char) < 127 for char in token):
                tokens.append(token)
        return tokens


class JwsArchiveReader(JwsReader):
    """
    Reads a zip or tar.gz archive containing one or more JASCO .jws files.

    Each .jws becomes one table, reusing JwsReader's parsing (_open_jws / _populate_spectrum).
    Since the titration volume is usually not a reliable instrument value, it is derived from the
    file name (falling back to the 'Sample name' metadata) and always recorded together with a
    Volume_flag, so a missing or dubious volume is recognizable instead of silently wrong.

    A volume expression is parsed as a main term plus optional additive terms joined by '+', e.g.
    'uL140+20water' -> main 140 uL, additive 20 uL water. Additives are captured explicitly (never
    dropped) and summed into volume_total_uL.
    """
    identifier = 'jws_archive_reader'
    # below asc_zip (10) and ascii_zip (10001); a strict check() keeps foreign archives out
    priority = 9

    # supported volume units and their conversion factor to microliter
    _UNIT_TO_UL = {'nl': 0.001, 'ul': 1.0, 'µl': 1.0, 'cl': 1e4, 'dl': 1e5, 'ml': 1e3, 'l': 1e6}
    # canonical display spelling per lowercase unit key
    _UNIT_DISPLAY = {'nl': 'nL', 'ul': 'µL', 'µl': 'µL', 'cl': 'cL', 'dl': 'dL', 'ml': 'mL', 'l': 'L'}
    _UNITS_RE = r'nl|ul|µl|cl|dl|ml|l'

    # a single volume token: number+unit or unit+number; trailing (?![a-z0-9]) guards the bare 'l'
    # so it is not matched inside words and 'ml'/'µl' are not read as a bare liter
    _volume_token = re.compile(
        rf'(?:(?P<num1>\d+(?:[.,]\d+)?)\s*(?P<unit1>{_UNITS_RE})'
        rf'|(?P<unit2>{_UNITS_RE})\s*(?P<num2>\d+(?:[.,]\d+)?))(?![a-z0-9])',
        re.IGNORECASE,
    )
    # an additive term following the main volume: '+ <number> <optional unit> <optional label>'
    _additive_pattern = re.compile(
        rf'^\s*\+\s*(?P<num>\d+(?:[.,]\d+)?)\s*(?P<unit>{_UNITS_RE})?\s*(?P<label>[a-z]*)',
        re.IGNORECASE,
    )
    _VOLUME_FALLBACK = 'n.a.'

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self._members = []  # list of (member_file, ole) for every valid .jws in the archive

    def check(self):
        """
        :return: True if the input is an archive containing at least one valid .jws file
        """
        if not self.is_tar_ball:
            return False

        self._members = []
        for member in self.file_content:
            if member.suffix.lower() == '.jws':
                ole = self._open_jws(member.content)
                if ole is not None:
                    self._members.append((member, ole))

        result = bool(self._members)
        logger.debug('result=%s', result)
        return result

    def prepare_tables(self):
        tables = []
        for member, ole in self._members:
            table = self.append_table(tables)
            self._populate_spectrum(ole, table)
            self._set_volume_metadata(table['metadata'], member.name)
        return tables

    def _set_volume_metadata(self, meta, filename):
        """Derive the volume from the file name, falling back to 'Sample name', then to n.a."""
        name = re.sub(r'\.jws$', '', filename, flags=re.IGNORECASE)
        info = self._parse_volume_expression(name)
        if info is None and meta.get('Sample name'):
            info = self._parse_volume_expression(str(meta['Sample name']))

        if info is None:
            meta['Volume'] = self._VOLUME_FALLBACK
            meta['volume_uL'] = self._VOLUME_FALLBACK
            meta['Volume_additives'] = ''
            meta['volume_total_uL'] = self._VOLUME_FALLBACK
            meta['Volume_flag'] = 'not_found'
            return

        meta['Volume'] = info['volume']
        meta['volume_uL'] = info['volume_uL']
        meta['Volume_additives'] = info['additives']
        meta['volume_total_uL'] = info['total_uL']
        meta['Volume_flag'] = info['flag']

    def _parse_volume_expression(self, text):
        """
        Parse a volume expression into a main term plus '+' additives.

        Returns a dict (volume, volume_uL, additives, total_uL, flag) or None if no volume token
        is present. flag is 'ok' (single term), 'additive' (one or more '+' additives captured), or
        'ambiguous' (an extra, non-additive volume token was found; it is still kept in additives).
        """
        main = self._volume_token.search(text)
        if main is None:
            return None

        num = main.group('num1') or main.group('num2')
        unit_key = (main.group('unit1') or main.group('unit2')).lower()
        main_ul = self._to_ul(num, unit_key)
        volume = f'{self._fmt(num)} {self._UNIT_DISPLAY[unit_key]}'

        additives = []
        total_ul = main_ul
        flag = 'ok'

        # consume consecutive additive terms directly following the main token
        rest = text[main.end():]
        while True:
            match = self._additive_pattern.match(rest)
            if match is None:
                break
            a_unit = (match.group('unit') or unit_key).lower()
            display = f"{self._fmt(match.group('num'))} {self._UNIT_DISPLAY[a_unit]}"
            label = (match.group('label') or '').strip()
            additives.append(f'{display} {label}'.strip())
            total_ul = self._sum_ul(total_ul, self._to_ul(match.group('num'), a_unit))
            flag = 'additive'
            rest = rest[match.end():]

        # a further volume token that is not a '+' additive is ambiguous, but keep it visible
        if self._volume_token.search(rest) is not None:
            flag = 'ambiguous'
            leftover = rest.strip(' -_')
            if leftover:
                additives.append(f'(unparsed: {leftover})')

        return {
            'volume': volume,
            # kept as numeric strings so metadata stays str-typed (matches the framework convention)
            'volume_uL': self._num_str(main_ul),
            'additives': '; '.join(additives),
            'total_uL': self._num_str(total_ul),
            'flag': flag,
        }

    @classmethod
    def _to_ul(cls, num_str, unit_key):
        """Convert a number string in the given unit to microliter, as int when whole."""
        value = float(num_str.replace(',', '.')) * cls._UNIT_TO_UL[unit_key]
        return int(value) if value == int(value) else round(value, 6)

    @staticmethod
    def _sum_ul(a, b):
        total = a + b
        return int(total) if total == int(total) else round(total, 6)

    @staticmethod
    def _num_str(value):
        """Format a microliter number as a clean numeric string ('140', '500.003')."""
        return str(int(value)) if value == int(value) else str(round(value, 6))

    @staticmethod
    def _fmt(num_str):
        """Normalize a number string for display (comma -> dot, drop a trailing '.0')."""
        value = num_str.replace(',', '.')
        return value[:-2] if value.endswith('.0') else value


Readers.instance().register(JwsReader)
Readers.instance().register(JwsArchiveReader)
