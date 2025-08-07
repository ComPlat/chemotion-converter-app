import inspect
from collections import OrderedDict

from converter_app.converters import logger
from converter_app.models import File, extract_tar_archive


class Readers:
    """
    This call manages all readers. It must be used as Singleton
    """
    _instance = None

    _registry = {
        'readers': {},
    }

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        """
        Singleton constructor
        :return: Readers Singleton
        """
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
        return cls._instance

    def register(self, reader):
        """
        Register reader
        :param reader: Object which implements reader/base
        :return:
        """
        if reader.identifier in self._registry['readers']:
            raise ValueError(f'Identifier ({reader.identifier}) is already registered')
        self._registry['readers'][reader.identifier] = reader

    @property
    def readers(self) -> OrderedDict:
        """
        Collects and lists all registered reader
        :return: A list of all readers
        """
        sorted_readers = sorted(self._registry['readers'].values(), key=lambda reader: reader.priority)
        return OrderedDict([(reader.identifier, reader) for reader in sorted_readers])

    def match_reader(self, file: File, ontology: str = None):
        """
        Checks which reader fits to a File
        :param file:
        :param ontology:
        :return:
        """

        print(f"Hello from match_reader: {file.name} as {ontology or 'unspecified'} file")

        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     file.name, file.content_type, file.mime_type, file.encoding)

        archive_file_list = extract_tar_archive(file)

        for _identifier, reader in self.readers.items():
            params = inspect.signature(reader).parameters
            if len(params) > 1:
                reader = reader(file, *archive_file_list)
            else:
                reader = reader(file)

            try:
                result = reader.check(ontology=ontology)
            except TypeError as e:
                if "unexpected keyword argument 'ontology'" in str(e):
                    result = reader.check()
                else:
                    raise  # other TypeErrors

            logger.debug('For reader %s -> result=%s', reader.__class__.__name__, result)

            # reset file pointer and return the reader it is the one
            file.fp.seek(0)
            for archive_file in archive_file_list:
                archive_file.fp.seek(0)
            if result:
                return reader

        return None
