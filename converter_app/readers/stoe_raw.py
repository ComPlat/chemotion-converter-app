import logging

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers
logger = logging.getLogger(__name__)

import struct
import numpy as np



class StoeRawReader(Reader):
    """
    Implementation of the TVB Reader for reading Stoe raw binary data file.
    Code was extracted from the TVB jupiter Notebook by Ron Dockhorn.
    # Beginn of Notebook
    # Simple Conversion of Stoe raw data file
    # by Ron Dockhorn (https://orcid.org/0000-0002-5268-5430)
    """
    identifier = 'stoe_raw_reader'
    priority = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contentrawfile = ''
        self._file_type = None

    @staticmethod
    def unpack_repeated_bytes(byte_data, data_type):
        """
        Unpack a series of bytes into a tuple of the same data type.

        :param byte_data: The bytes to unpack.
        :param data_type: The format character for the data type (e.g., 'b' for signed char).
        :return: A tuple of unpacked values.
        """
        # Create the format string based on the data type and count
        # 'i': Integer (4 bytes)
        # 'f': Float (4 bytes)
        # 'd': Double (8 bytes)
        # 'h': Short (2 bytes)
        # 'b': Signed char (1 byte)
        # 'B': Unsigned char (1 byte)
        # 'q': Long long (8 bytes)
        # 'Q': Unsigned long long (8 bytes)

        if data_type == 'b':
            count = len(byte_data)
        elif data_type == 'h':
            count = len(byte_data) // 2
        elif data_type in ['i', 'f']:
            count = len(byte_data) // 4
        else:
            raise ValueError(f'{data_type} not supported')

        format_string = f'{count}{data_type}'

        # Unpack the byte data using the constructed format string
        return struct.unpack(format_string, byte_data)

    @staticmethod
    def get_non_empty_chunks_separated_by_null(data_slice):
        """
        Get all non-empty chunks of data separated by NULL bytes.

        :param data_slice: The slice of data to split.
        :return: A list of bytes objects, each representing a non-empty chunk of data.
        """
        # Split the data by NULL bytes and filter out empty chunks
        return [chunk for chunk in data_slice.split(b'\x00') if chunk]

    def get_file_type_version(self):
        ###
        # File Type Version
        ###

        self.contentrawfile = self.file.content

        unpacked_data = self.unpack_repeated_bytes(self.contentrawfile[0x00:0x0D + 1], 'b')

        # Convert unpacked data to a string
        string_output_file_type = ''.join(chr(b) for b in unpacked_data)

        return string_output_file_type

    def check(self):
        """
        :return: True if it fits
        """

        return (
                self.file.suffix.lower() == ".raw"
                and self.file.encoding.lower() == "binary"
                and self.file_type == "RAW_1.06Powdat"
        )

    @property
    def file_type(self):
        if self._file_type is None:
            self._file_type = self.get_file_type_version()
        return self._file_type

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        table['metadata']['File Type'] = self.file_type

        ###
        # Date of Experiment
        ###

        datasplice = self.contentrawfile[0x0010:0x001F + 1]
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'b')

        # Convert unpacked data to a string
        string_output_day = ''.join(chr(b) for b in unpacked_data)

        table['metadata']['Ex date'] = string_output_day.split()[0].strip()
        table['metadata']['Ex time'] = string_output_day.split()[1].strip()

        ###
        # File Name And Comments?
        ###
        datasplice = self.contentrawfile[0x0020:0x012F + 1]

        # Get all chunks separated by NULL bytes in the data slice
        chunks = self.get_non_empty_chunks_separated_by_null(datasplice)

        # Only add description if nothing is there
        description = ''

        # Print the result chunks
        for i, chunk in enumerate(chunks):
            unpacked_data = self.unpack_repeated_bytes(chunk, 'b')
            string_output_description = ''.join(chr(b) for b in unpacked_data)
            # Print the unpacked data as a string
            # The comments in the file is not needed - uncomment if necessary
            description += string_output_description + '\n'

        for line in description.split('\n'):
            clean_line = line.strip()
            if clean_line:
                table['header'].append(clean_line)

        ###
        # Experimental setup
        # Copper K Alpha1 x-ray wavelength of 1.5406 Angstrom used by the experiment.
        ###
        datasplice = self.contentrawfile[0x0142:0x014A]
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'f')

        table['metadata']['Alpha1 x-ray wavelength'] = str(unpacked_data[0])

        ###
        # Start and End Time Experiment
        ###
        datasplice = self.contentrawfile[4 * 0x10000 + 0x0600:4 * 0x10000 + 0x0620]
        # Get all chunks separated by NULL bytes in the data slice
        chunks = self.get_non_empty_chunks_separated_by_null(datasplice)

        for i, chunk in enumerate(chunks):
            unpacked_data = self.unpack_repeated_bytes(chunk, 'b')
            string_output_time = ''.join(chr(b) for b in unpacked_data)
            if i == 0:
                table['metadata']['Start date'] = string_output_time.split()[0].strip()
                table['metadata']['Start time'] = string_output_time.split()[1].strip()
            if i == 1:
                table['metadata']['End date'] = string_output_time.split()[0].strip()
                table['metadata']['End time'] = string_output_time.split()[1].strip()

        ###
        # Number of Data Entries
        ###
        datasplice = self.contentrawfile[4 * 0x10000 + 0x0622:4 * 0x10000 + 0x0624]
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'h')
        count_data_entries = int(unpacked_data[0])
        table['metadata']['Data entries'] = str(count_data_entries)

        ###
        # x-range: 2Theta
        ###
        datasplice = self.contentrawfile[4 * 0x10000 + 0x062C:4 * 0x10000 + 0x0638]

        unpacked_data = self.unpack_repeated_bytes(datasplice, 'f')

        x_start = unpacked_data[0]
        x_end = unpacked_data[2]

        x_range = np.linspace(x_start, x_end, count_data_entries, True)

        ###
        # Data: Intensity counts
        ###

        datasplice = self.contentrawfile[0x40800:0x40800 + 4 * count_data_entries]

        unpacked_data = self.unpack_repeated_bytes(datasplice, 'i')

        y_data = np.array(unpacked_data, dtype=np.int64)

        columns = [x_range, y_data]
        table['rows'] = [[float(x), int(y)] for x, y in zip(*columns)]

        return tables


Readers.instance().register(StoeRawReader)