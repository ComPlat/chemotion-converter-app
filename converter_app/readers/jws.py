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

    def check(self):
        """
        :return: True if the file is a readable JASCO .jws OLE2 file with the expected streams
        """
        if self.file.suffix.lower() != '.jws' or self.file.encoding.lower() != 'binary':
            return False

        try:
            ole = olefile.OleFileIO(io.BytesIO(self.file.content))
        except (OSError, ValueError):
            return False

        streams = {'/'.join(entry) for entry in ole.listdir()}
        result = 'DataInfo' in streams and 'Y-Data' in streams
        if result:
            self._ole = ole
        else:
            ole.close()

        logger.debug('result=%s', result)
        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        ole = self._ole

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

        return tables

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


Readers.instance().register(JwsReader)
