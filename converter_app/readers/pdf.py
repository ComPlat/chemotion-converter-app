import logging
import tempfile
import fitz
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class PdfReader(Reader):
    """
    Tries to read PDF file generally. However, in most cases it is necessary to write a mor specific reader
    """
    identifier = 'pdf_reader'
    priority = 100

    def __init__(self, file):
        super().__init__(file)
        self.text_data = None

    def check(self):
        result = self.file.suffix == '.pdf'
        if result:
            self.text_data = self._read_pdf()
        return result

    def _get_pdf_content(self):
        try:
            return self.file.features('text_data')
        except AttributeError:
            with tempfile.NamedTemporaryFile(delete=True) as temp_pdf:
                try:
                    # Save the contents of FileStorage to the temporary file
                    self.file.fp.save(temp_pdf.name)

                    # Open the PDF file using PyMuPDF
                    res = fitz.open(temp_pdf.name)
                    self.file.set_features('text_data', res)
                    return res
                    # Access and manipulate the document using doc

                    # Close the document when you're done
                except:
                    return {}
                finally:
                    # Remove the temporary file
                    temp_pdf.close()

    def _read_pdf(self):
        doc = self._get_pdf_content()
        current_section = []
        text_data = {'_': current_section}

        link = doc.outline
        for page_num in range(doc.page_count):
            page = doc[page_num]
            blocks = page.get_text('blocks')

            if link is not None and link.page < page_num:
                current_section = {}
                text_data[link.title] = current_section
                link = link.next

            for block in blocks:
                line = block[4]
                if link is not None and link.y <= block[1] and link.page == page_num:
                    current_section = []
                    text_data[link.title.strip()] = current_section
                    link = link.next

                current_section.append(self.prepare_line(line))

        return text_data

    def prepare_line(self, line):
        """
        :param line: PDF line string
        :return: dict: basic construct to contain line metadata
        """
        split_line = [x for x in line.split('\n') if x != '']
        text_obj = {'text': line.replace('\n', ' ').strip(), 'meta': {}}
        if len(split_line) >= 2:
            text_obj['meta'][split_line[0]] = ' '.join(split_line[1:])
        return text_obj

    def prepare_tables(self):
        tables = []
        text_data = self.text_data
        for table_name, pdf_data in text_data.items():
            table = self.append_table(tables)

            table['metadata']['___SECTION'] = table_name
            for line in pdf_data:
                table['header'].append(line['text'])
                for k, v in line['meta'].items():
                    table['metadata'].add_unique(k, v)

        return tables


Readers.instance().register(PdfReader)
