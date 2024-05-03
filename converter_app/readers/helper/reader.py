from collections import OrderedDict

from converter_app.converters import logger
from converter_app.models import File


class Readers:
    """
    This calls manages all reader. It must be used as Singleton
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
            print('Creating new instance')
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
        :return: A list of all reader
        """
        sorted_readers = sorted(self._registry['readers'].values(), key=lambda reader: reader.priority)
        return OrderedDict([(reader.identifier, reader) for reader in sorted_readers])

    def match_reader(self, file: File):
        """
        Checks which reader fits to a File
        :param file:
        :return:
        """
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     file.name, file.content_type, file.mime_type, file.encoding)

        for _identifier, reader in self.readers.items():
            reader = reader(file)
            result = reader.check()

            logger.debug('For reader %s -> result=%s', reader.__class__.__name__, result)

            # reset file pointer and return the reader it is the one
            file.fp.seek(0)
            if result:
                return reader

        return None
