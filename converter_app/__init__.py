import importlib.metadata
import json
import os
import mimetypes
from pathlib import Path
from typing import Literal

from werkzeug.datastructures import FileStorage

os.environ["TYPEGUARD_DISABLE"] = "1"

TITLE = importlib.metadata.distribution('chemotion-converter-app').name
VERSION = importlib.metadata.version('chemotion-converter-app')

if __name__ == '__main__':
    print(f"{TITLE} version {VERSION}")
else:

    def read(path: Path | str) -> dict:
        """
        Read a data file and return it as a standardized, convertible dictionary.

        This method reads a file and converts its contents into an internal
        data structure that can be further transformed into standardized
        file formats.

        The returned dictionary has two top-level keys:

        - ``metadata``: Information about the input file.
        - ``tables``: A list of parsed data tables extracted from the file.

        **Metadata structure**
        ``metadata`` contains file-related information, for example::

            {
                "file_name": "01_CV.DTA",
                "content_type": "application/octet-stream",
                "mime_type": "text/plain",
                "extension": ".DTA",
                "reader": "DtaReader",
                "uploaded": "2026-03-02T09:08:37.765475+00:00"
            }

        **Tables structure**
        ``tables`` is a list of table objects. Each table contains:

        - ``header``: A list of raw input lines from the file header.
        - ``metadata``: A dictionary with preprocessed and specialized
          table-level metadata.
        - ``columns``: A list of column definitions. Each column contains:
            - ``key``: A unique identifier for the column
            - ``name``: A human-readable column name
        - ``rows``: A list of rows containing the data values, ordered
          according to the ``columns`` definition.

        :param path: path to raw data file
        :return: dict: A standardized dictionary containing file metadata and
            parsed table data.
        """

        from converter_app.readers.helper.reader import Readers
        from converter_app.models import File
        input_file_path = Path(path)
        if not input_file_path.exists():
            raise ValueError(f"{path} does not exist!")
        if input_file_path.is_dir():
            raise IsADirectoryError(f"{path} is a directory!")
        content_type, _ = mimetypes.guess_type(input_file_path.name)
        content_type = content_type or "application/octet-stream"
        with open(input_file_path, 'rb') as f:
            content_length = os.fstat(f.fileno()).st_size
            fs = FileStorage(stream=f, filename=input_file_path.name, content_type=content_type,
                             content_length=content_length, )
            file = File(fs)
            reader = Readers.instance().match_reader(file)
            if not reader:
                raise ValueError(f"No reader available for {input_file_path}")
            reader.process()
            return reader.as_dict

    def convert(raw_file: Path | str, profile_path: Path | str, output = Literal['jcampzip', 'rdf']) -> bytes:
        """
        Read a data file and return it as converted binary file.

        Usage rdf::

        >>> raw_file = '/path/to/raw-file'
        >>> profile_path = '/path/to/profile/eba5538f-46ec-4361-b231-72399b6db8f6.json'
        >>> file_content = convert(raw_file, profile_path, 'rdf')
        >>> with open('result.ttl', 'wb+') as f:
        >>>     f.write(file_content)

        Usage bagit.zip::

        >>> raw_file = '/path/to/raw-file'
        >>> profile_path = '/path/to/profile/eba5538f-46ec-4361-b231-72399b6db8f6.json'
        >>> file_content = convert(raw_file, profile_path, 'jcampzip')
        >>> with open('bagit.zip', 'wb+') as f:
        >>>     f.write(file_content)

        :param raw_file: path to raw data file
        :param profile_path: Path to a ChemConverter profile json file.
        :param output: Output type: jcampzip for .zip Bagit archive and  or rdf for a .ttl file.
        :return: Converted file content as bytes
        """
        from converter_app.converters import Converter
        from converter_app.models import Profile
        from converter_app.utils import run_conversion
        reader_dict = read(raw_file)
        with open(profile_path, 'r') as f:
            json_data = json.load(f)
        prof = Profile(json_data, 'cli', json_data.get('id'))
        converter =  Converter(prof, reader_dict)
        writer = run_conversion(converter, output)
        return writer.write()

__all__ = [
    "convert",
    "read",
    "TITLE",
    "VERSION",
]
