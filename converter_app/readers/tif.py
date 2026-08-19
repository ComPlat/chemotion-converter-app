import io
import logging
import re

import magic
from PIL import Image, UnidentifiedImageError
from PIL.TiffTags import TAGS
from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

# Only strings longer than this are treated as an embedded header blob.
# Shorter string tags (e.g. ``Software``) are kept as plain metadata.
HEADER_BLOB_MIN_LEN = 32

# TIFF tags whose value is structurally redundant or too large to be useful
# as metadata (e.g. the colour palette).
SKIP_METADATA_TAGS = frozenset({320})  # ColorMap


class TifReader(Reader):
    """
    Reads metadata from TIFF image files.

    Image properties are taken from the standard TIFF tags. Embedded headers
    (vendor blocks such as ZEISS' key=value block or an XML document in the
    ImageDescription tag) are routed through the regular converter workflow:
    every structured header is wrapped in a temporary :class:`File` whose
    extension is sniffed from its content, matched against the registered
    readers and the resulting tables are merged back into this reader's output.
    Unstructured ``key = value`` headers keep being parsed in place.
    """
    identifier = 'tif_reader'
    priority = 96

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self._image_tags = None
        self._header_blobs = None

    def check(self):
        if self.file.suffix.lower() not in ('.tif', '.tiff'):
            return False
        if self.file.mime_type != 'image/tiff':
            return False
        try:
            self._read_tiff_tags()
        except (UnidentifiedImageError, OSError, ValueError) as err:
            logger.debug('Could not read TIFF tags from %s: %s', self.file.name, err)
            return False
        return self._image_tags is not None

    def _read_tiff_tags(self) -> None:
        """
        Reads the TIFF tags via Pillow and splits them into plain image
        metadata and (long) embedded header blobs.
        """
        image_tags = {}
        header_blobs = []
        with Image.open(io.BytesIO(self.file.content)) as image:
            for tag_id, value in image.tag_v2.items():
                name = TAGS.get(tag_id, str(tag_id))
                if isinstance(value, str):
                    # TIFF text tags are NUL-padded to a fixed size; interior
                    # NUL bytes indicate a binary blob (e.g. a UTF-16 encoded
                    # duplicate) which we skip.
                    text = value.rstrip('\x00').strip()
                    if '\x00' in text:
                        continue
                    if len(text) > HEADER_BLOB_MIN_LEN:
                        header_blobs.append((tag_id, name, text))
                        continue
                    if text:
                        image_tags[name] = text
                    continue
                if tag_id in SKIP_METADATA_TAGS:
                    continue
                if isinstance(value, (tuple, list)):
                    str_value = ', '.join(str(v) for v in value)
                else:
                    str_value = str(value)
                if str_value.strip():
                    image_tags[name] = str_value
        self._image_tags = image_tags
        self._header_blobs = header_blobs

    @staticmethod
    def _sniff_suffix(text: str) -> str | None:
        """
        Guesses a file extension for an embedded header from its content so the
        normal reader matching can pick the right reader. Returns ``None`` for
        unstructured text (handled in place as ``key = value``).
        """
        head = text.lstrip('﻿ \t\r\n')[:256]
        if head.startswith('<?xml') or re.match(r'<[A-Za-z][\w.:-]*[\s/>]', head):
            return '.xml'
        if head[:1] in ('{', '['):
            return '.json'
        return None

    def get_value(self, value):
        if self.float_de_pattern.match(value):
            # remove any digit group seperators and replace the comma with a period
            return value.replace('.', '').replace(',', '.')
        if self.float_us_pattern.match(value):
            # just remove the digit group seperators
            return value.replace(',', '')
        return None

    def _delegate_header(self, name: str, text: str, tables: list) -> bool:
        """
        Wraps a structured header in a temporary :class:`File`, runs it through
        the regular reader matching and appends the resulting tables. Returns
        ``True`` if a reader handled the header.
        """
        suffix = self._sniff_suffix(text)
        if suffix is None:
            return False

        data = text.encode('utf-8', errors='ignore')
        mime_type = magic.Magic(mime=True).from_buffer(data)
        file_storage = FileStorage(stream=io.BytesIO(data),
                                   filename=f'{self.file.name}{suffix}',
                                   content_type=mime_type)
        # The header is never a TIFF, so this cannot recurse into TifReader.
        reader = Readers.instance().match_reader(File(file_storage))
        if reader is None:
            return False

        logger.debug('Embedded header %s of %s handled by %s',
                     name, self.file.name, reader.identifier)
        header_tables = reader.prepare_tables()
        for header_table in header_tables:
            header_table.add_metadata('embedded_header_tag', name)
            header_table.add_metadata('embedded_header_reader', reader.identifier)
            tables.append(header_table)
        return bool(header_tables)

    def _parse_key_value_blob(self, text: str, table) -> None:
        """
        Parses an unstructured header as ``key = value`` lines; standalone
        numeric lines become rows.
        """
        for raw_line in text.replace('\r\n', '\n').split('\n'):
            line = raw_line.strip()
            if not line:
                continue
            table['header'].append(line)
            if '=' in line:
                key, value = line.split('=', 1)
                table['metadata'][key.strip()] = value.strip()
                continue
            num_val = self.get_value(line)
            if num_val is not None:
                try:
                    num_val = float(num_val)
                except ValueError:
                    pass
                table['rows'].append([len(table['rows']), num_val])

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        for key, value in self._image_tags.items():
            table['metadata'][key] = value

        for _tag_id, name, text in self._header_blobs:
            if not self._delegate_header(name, text, tables):
                self._parse_key_value_blob(text, table)

        if table['rows']:
            table['columns'].append({'key': '0', 'name': 'Idx'})
            table['columns'].append({'key': '1', 'name': 'Number'})

        return tables


Readers.instance().register(TifReader)
