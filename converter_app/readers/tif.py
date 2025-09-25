import logging
import re
from typing import List, Dict

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

UNIT_EXTENSION = "_unit"


class TifReader(Reader):
    """
    Reads metadata from Tiff file images
    """
    identifier = 'tif_reader'
    priority = 96


    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self._parsed_values = None

    def check(self):
        result = False
        if self.file.suffix.lower() == '.tif' and self.file.mime_type == 'image/tiff':
            self._parsed_values = self._read_img()
            result = self._parsed_values is not None and len(self._parsed_values) > 0
        return result

    # xml-tag parser ------------------------------------------------------------------------------
    def _xml_init_state(self):
        self._xml_stack: List[str] = []
        # store raw values as lists per key (path)
        self._xml_vals: Dict[str, List[str]] = {}
        # per-element text buffer until the closing tag happens
        self._xml_buf: Dict[str, List[str]] = {}

    def _xml_put(self, path: str, value: str) -> None:
        # collapse inner whitespace once
        value = re.sub(r"\s+", " ", value).strip()
        if not value:
            return
        self._xml_vals.setdefault(path, []).append(value)

    def _xml_norm(self, s: str) -> str:
        s = s.strip()
        s = re.sub(r"<\\\s*([A-Za-z0-9:_\-]+)\s*>", r"</\1>", s)  # <\b> -> </b>
        s = re.sub(r"\s+>", ">", s)
        return s

    def _xml_is_taglike(self, text: str) -> bool:
        return text.lstrip().startswith("<") and ">" in text

    def _xml_tag_name(self, tag: str) -> str:
        tag = tag.strip("<>/ ")
        tag = tag.split()[0]
        if ":" in tag:
            tag = tag.split(":", 1)[1]
        return tag

    def _xml_path(self, leaf: str | None = None) -> str:
        parts = self._xml_stack[:]
        if leaf:
            parts.append(leaf)
        return ".".join(parts)

    def _xml_open(self, name: str) -> None:
        self._xml_stack.append(name)
        path = self._xml_path()
        # start a fresh buffer for this element
        self._xml_buf[path] = []

    def _xml_text(self, text: str) -> None:
        text = text  # raw; normalize at commit time
        path = self._xml_path()
        if path in self._xml_buf:
            self._xml_buf[path].append(text)

    def _xml_close(self, name: str) -> None:
        # pop until we close 'name' (lenient)
        while self._xml_stack:
            curr = self._xml_stack[-1]
            path = self._xml_path()  # path BEFORE popping (current element)
            # commit buffered text for current element (if any)
            if path in self._xml_buf:
                joined = "".join(self._xml_buf.pop(path))
                # normalize whitespace now and emit to _xml_kv
                self._xml_put(path, joined)
            self._xml_stack.pop()
            if curr == name:
                break

    def _xml_selfclose(self, name: str) -> None:
        # open -> commit empty -> close
        self._xml_open(name)
        self._xml_close(name)

    def _xml_handle_line(self, parts: List[str]) -> bool:
        """
        Consume one tokenized line as XML.
        Returns True if handled as XML (so caller should skip non-XML handling).
        """
        line = "".join(str(p) for p in parts)
        line = self._xml_norm(line)
        if not self._xml_is_taglike(line):
            return False

        # Tokenize into tags and text
        for tok in re.finditer(r"<[^>]+>|[^<]+", line):
            s = tok.group(0)
            if s.startswith("<"):
                # classify tag
                if s.startswith("</"):  # closing tag
                    name = self._xml_tag_name(s)
                    self._xml_close(name)
                else:
                    selfclosing = s.endswith("/>")
                    name = self._xml_tag_name(s)
                    if selfclosing:
                        self._xml_selfclose(name)
                    else:
                        self._xml_open(name)
            else:
                # text between tags -> append to current element buffer
                t = s
                # preserve spaces; final normalization happens at commit
                if t.strip():  # ignore pure whitespace nodes
                    self._xml_text(t)

        return True

    # end of xml-tag parser ------------------------------------------------------------------------------

    def _read_img(self):
        txt = re.sub(r'\\x[0-9a-f]{2}', '', str(self.file.content))

        txt = re.sub(r'^.+@@@@@@0\\r\\n', '', txt)
        lines = re.split(r'\\r\\n', txt)
        del lines[-1]
        return [x.split('=') for x in lines]

    def get_value(self, value):
        if self.float_de_pattern.match(value):
            # remove any digit group seperators and replace the comma with a period
            return value.replace('.', '').replace(',', '.')
        if self.float_us_pattern.match(value):
            # just remove the digit group seperators
            return value.replace(',', '')

        return None

    def prepare_tables(self):
        # Initialize XML state once per run
        if not hasattr(self, "_xml_stack"):
            self._xml_init_state()

        tables = []
        table = self.append_table(tables)

        for val in self._parsed_values:
            # Try XML first (returns True if the line was XML-like and handled)
            if self._xml_handle_line(val):
                table['header'].append(f"{'='.join(val)}")
                continue
            if len(val) == 1:
                num_val = self.get_value(val[0])
                if num_val is not None:
                    table['rows'].append([len(table['rows']), float(num_val)])
            elif str(val).count("@") > 5: # skip picture code itself
                continue
            else:
                table['metadata'][val[0]] = '='.join(val[1:])
            table['header'].append(f"{'='.join(val)}")

        table['columns'].append({
            'key': '0',
            'name': 'Idx'
        })
        table['columns'].append({
            'key': '1',
            'name': 'Number'
        })

        for k, arr in self._xml_vals.items():
            if len(arr) == 1:
                table['metadata'][k] = str(arr[0])
            else:
                table['metadata'][k] = str(arr)

        return tables


Readers.instance().register(TifReader)
