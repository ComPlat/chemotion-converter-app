import inspect

import magic
from werkzeug.datastructures import FileStorage

from converter_app.models import File, extract_tar_archive
from converter_app.readers import READERS


class TestReader:
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
        file = File(fs)
        archive_file_list = extract_tar_archive(file)
        reader_class = READERS.readers[self.reader_id]
        params = inspect.signature(reader_class).parameters
        if len(params) > 1:
            reader = reader_class(file, *archive_file_list)
        else:
            reader = reader_class(file)
        assert reader.check()
        reader.process()
        return reader

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
