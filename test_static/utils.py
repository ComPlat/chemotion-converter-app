import magic
from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers import READERS


class ManageTestReader:
    def __init__(self, test_file_path: str, reader_id: str):
        self.test_file_path = test_file_path
        self.reader_id = reader_id
        self.storage = None

    def __enter__(self):
        self.storage = open(self.test_file_path, 'rb')
        mime_type = magic.Magic(mime=True).from_buffer(self.storage.read())
        self.storage.seek(0)
        fs = FileStorage(stream=self.storage, filename=self.test_file_path,
                         content_type=mime_type)
        temp_readers = READERS.readers
        READERS.readers = {self.reader_id : READERS.readers[self.reader_id]}
        try:
            reader = READERS.match_reader(File(fs))
            assert reader.identifier == self.reader_id
            reader.process()
            return reader
        finally:
            READERS.readers = temp_readers


    def __exit__(self, exc_type, exc_value, traceback):
        # Cleanup the storage resource (close the file, etc.)
        print(f"Closing storage at {self.test_file_path}")
        if self.storage:
            self.storage.close()

        # Handle any exceptions if necessary
        if exc_type:
            print(f"Exception type: {exc_type}")
            print(f"Exception value: {exc_value}")
            return False  # Allow exceptions to propagate (if you want them to)
        return True  # Suppress exceptions (if you want to handle them)
