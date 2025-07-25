from abc import ABC, abstractmethod


class Writer(ABC):
    """
    Processes a reader output and prepares all gained date in a single file
    """
    def __init__(self, converter):
        self.tables = converter.tables
        self._converter = converter

    @abstractmethod
    def write(self) -> bytes:
        """
        Returns the whole file content as bytes
        :return: Files content to be sent
        """

    @abstractmethod
    def process(self):
        """
        Processes the reader output
        """
