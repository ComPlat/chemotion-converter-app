import logging
import re
from typing import List, Dict, Any

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
        # Call this once per file/section before the loop if needed
        self._xml_stack: List[str] = []
        self._xml_kv: Dict[str, Any] = {}

    def _xml_norm(self, s: str) -> str:
        # Normalize "<\tag>" -> "</tag>", trim stray spaces before '>'
        s = s.strip()
        s = re.sub(r"<\\\s*([A-Za-z0-9:_\-]+)\s*>", r"</\1>", s)
        s = re.sub(r"\s+>", ">", s)
        return s

    def _xml_is_taglike(self, text: str) -> bool:
        # Heuristic: looks like XML-ish content
        return text.lstrip().startswith("<") and ">" in text

    def _xml_tag_name(self, tag: str) -> str:
        # Extract element name without namespace and without attributes
        # e.g. "<TemReporter xmlns:xsd" -> "TemReporter"
        # e.g. "<a>" -> "a"
        tag = tag.strip("<>/ ")
        tag = tag.split()[0]
        # strip namespace prefix "x:Tag" -> "Tag" (keep local part)
        if ":" in tag:
            tag = tag.split(":", 1)[1]
        return tag

    def _xml_path(self, leaf: str | None = None) -> str:
        parts = self._xml_stack[:]
        if leaf:
            parts.append(leaf)
        return ".".join(parts)

    def _xml_put(self, path: str, value: str) -> None:
        if path in self._xml_kv:
            if isinstance(self._xml_kv[path], list):
                self._xml_kv[path].append(value)
            else:
                self._xml_kv[path] = [self._xml_kv[path], value]
        else:
            self._xml_kv[path] = value

    def _xml_handle_line(self, parts: List[str]) -> bool:
        """
        Try to consume one tokenized line as XML.
        Returns True if handled as XML, else False (so caller can process non-XML cases).
        """
        line = "".join(str(p) for p in parts)
        line = self._xml_norm(line)
        if not self._xml_is_taglike(line):
            return False

        # Handle compact forms: <a>text</a>, <b>, </b>, self-closing <a/>
        # There may also be multiple tags on one line; iterate.
        i = 0
        handled_any = False
        for m in re.finditer(r"<[^>]+>|[^<]+", line):
            tok = m.group(0)
            if tok.startswith("<"):
                handled_any = True
                if tok.startswith("</"):  # closing
                    name = self._xml_tag_name(tok)
                    if self._xml_stack and self._xml_stack[-1] == name:
                        self._xml_stack.pop()
                    else:
                        # lenient: try to pop until match
                        if name in self._xml_stack:
                            while self._xml_stack and self._xml_stack[-1] != name:
                                self._xml_stack.pop()
                            if self._xml_stack and self._xml_stack[-1] == name:
                                self._xml_stack.pop()
                    continue

                # opening or self-closing
                selfclosing = tok.endswith("/>")
                name = self._xml_tag_name(tok)
                if name:
                    self._xml_stack.append(name)
                if selfclosing:
                    # Immediately emit empty value for self-closing element if no text follows
                    path = self._xml_path()
                    # record empty string if not present yet (only if meaningful to you)
                    if path not in self._xml_kv:
                        self._xml_put(path, "")
                    # Pop the self-closed tag
                    if self._xml_stack and self._xml_stack[-1] == name:
                        self._xml_stack.pop()
            else:
                # text node between tags
                text = tok.strip()
                if text:
                    path = self._xml_path()
                    # If text belongs to an element like <a>text</a>, the current path is correct.
                    self._xml_put(path, text)
        return handled_any

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

        for k, v in self._xml_kv.items():
            table['metadata'][k] = v

        return tables


Readers.instance().register(TifReader)
