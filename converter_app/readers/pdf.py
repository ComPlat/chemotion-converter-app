import logging
import tempfile
from .base import Reader
import fitz # imports the pymupdf library

logger = logging.getLogger(__name__)


class PdfReader(Reader):
    identifier = 'pdf_reader'
    priority = 1

    def check(self):
        result =  self.file.encoding == 'binary' and self.file.suffix == '.pdf'

        logger.debug('result=%s', result)
        return result

    def _read_pdf(self):
        temp_pdf = tempfile.NamedTemporaryFile(delete=False)

        try:
            # Save the contents of FileStorage to the temporary file
            self.file.fp.save(temp_pdf.name)

            # Open the PDF file using PyMuPDF
            doc = fitz.open(temp_pdf.name)

            # Access and manipulate the document using doc

            # Close the document when you're done
        except:
            return {}
        finally:
            # Remove the temporary file
            temp_pdf.close()
        current_section = []
        text_data = {'_': current_section }


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
                split_line = [x for x in line.split('\n') if x != '']
                text_obj = {'text': line.replace('\n' ,' ').strip(), 'meta': {}}
                if len(split_line) >= 2:
                    text_obj['meta'][split_line[0]] = ' '.join(split_line[1:])
                current_section.append(text_obj)

        doc.close()

        return text_data


    def get_tables(self):
        tables = []
        text_data = self._read_pdf()
        for table_name, pdf_data in text_data.items():
            table = self.append_table(tables)

            table['metadata']['___SECTION'] = table_name
            for line in pdf_data:
                table['header'].append(line['text'])
                table['metadata'] |= line['meta']


        return tables