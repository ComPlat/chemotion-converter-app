import logging

from converter_app.readers.helper.reader import Readers
from converter_app.readers.ascii import AsciiReader

logger = logging.getLogger(__name__)

import struct
import numpy as np
import xmltodict



class TvbReader(AsciiReader):
    """
    Implementation of the TVB Reader for reading Raman binary TVB files.
    Code was extracted from the TVB jupiter Notebook by Ron Dockhorn.
    # Beginn of Notebook
    # Simple Conversion of TriVista tvb data file
    # by Ron Dockhorn (https://orcid.org/0000-0002-5268-5430)
    """
    identifier = 'tvb_reader'
    priority = 5

    def unpack_repeated_bytes(self, byte_data, data_type, count, littleEndianEncoding=True):
        """
        Unpack a series of bytes into a tuple of the same data type.
        'i': Integer (4 bytes)
        'I': Unsigned Int (4 bytes)
        'l': Long (4 bytes)
        'L': Long (8 bytes)
        'f': Float (4 bytes)
        'd': Double (8 bytes)
        'h': Short (2 bytes)
        'b': Signed char (1 byte)
        'B': Unsigned char (1 byte)
        'q': Long long (8 bytes)
        'Q': Unsigned long long (8 bytes)

        :param byte_data: The bytes to unpack.
        :param data_type: The format character for the data type (e.g., 'b' for signed char).
        :param count: The number of items to unpack.
        :param littleEndianEncoding: Flag to determine if the data is in little-endian format.
        :return: A tuple of unpacked values.
        """
        # Determine the endianness based on the flag
        endianness = '<' if littleEndianEncoding else '>'

        # Create the format string based on the data type, count, and endianness
        format_string = f'{endianness}{count}{data_type}'

        # Unpack the byte data using the constructed format string
        return struct.unpack(format_string, byte_data)

    def get_non_empty_chunks_separated_by_null(self, data_slice):
        """
        Get all non-empty chunks of data separated by NULL bytes.

        :param data_slice: The slice of data to split.
        :return: A list of bytes objects, each representing a non-empty chunk of data.
        """
        # Split the data by NULL bytes and filter out empty chunks
        return [chunk for chunk in data_slice.split(b'\x00') if chunk]

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix.lower() == ".tvb" and self.file.encoding.lower() == "binary"

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        contentTVBfile = self.file.content

        # print(f'Length TVB files (bytes): {len(contentTVBfile)} ({hex(len(contentTVBfile))})')
        _bytes_length = (len(contentTVBfile), hex(len(contentTVBfile)))

        ###
        # File Type Version
        ###
        datasplice = contentTVBfile[0x0000:0x003]  # this should be 'tvb'
        # 'b': Signed char (1 byte)
        count = len(datasplice) // 1  # Number of bytes to unpack (1 for char)
        # print(count)
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'b', count)
        string_output_file_type = ''.join(chr(b) for b in unpacked_data)
        table['metadata']['File Type'] = str(string_output_file_type)
        # print(string_output_file_type)
        if not string_output_file_type == "tvb":
            return []

        ###
        # File Info - Frames and Dataset Length
        ###
        datasplice = contentTVBfile[0x0004:0x0016]
        # 'i': Integer (4 bytes)
        # 'f': Float (4 bytes)
        # 'd': Double (8 bytes)
        # 'h': Short (2 bytes)
        count = len(datasplice) // 2  # Number of bytes to unpack (1 for char)
        # print(count)
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'h', count, littleEndianEncoding=True)

        numDatasetLength = int(unpacked_data[1])
        numFrames = int(unpacked_data[5])

        table['metadata']['Unpacked data'] = str(unpacked_data)
        # print(unpacked_data)
        # print(f'Datalength: {numDatasetLength}', f'Frames: {numFrames}')
        table['metadata']['Datalength'] = str(numDatasetLength)
        table['metadata']['Frames'] = str(numFrames)

        ###
        # LaserExcitationWavelength
        ###
        datasplice = contentTVBfile[0x0025:0x002D]
        # 'd': double (8 byte)
        count = len(datasplice) // 8  # Number of bytes to unpack (1 for char)
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'd', count)

        LaserExcitationWavelength = float(unpacked_data[0])  # in nanometer
        # print(f'LaserExcitationWavelength [nm]: {LaserExcitationWavelength}')
        table['metadata']['LaserExcitationWavelength [nm]'] = str(LaserExcitationWavelength)

        ###
        # Number of Raman Wavelength entries = NRWE
        ###
        datasplice = contentTVBfile[0x002D:0x0031]
        # 'I': unsigned integer (4 byte)
        count = len(datasplice) // 4  # Number of bytes to unpack (1 for char)

        unpacked_data = self.unpack_repeated_bytes(datasplice, 'I', count)

        NRWE = int(unpacked_data[0])
        # print(f'Number of Raman Wavelength entries: {NRWE}')
        table['metadata']['Number of Raman Wavelength entries'] = str(NRWE)

        ###
        # List of Raman Wavelength [in nm] convert to Raman Shift = Raman Wavenumber [1/nm]
        # $$\Delta \omega [cm^{-1}] = ( \frac{1}{\lambda_{laser}} - \frac{1}{\lambda_{}}) \cdot 10⁷   $$
        ###
        datasplice = contentTVBfile[0x0031:0x0031 + 4 * NRWE]
        # 'f': float (4 byte)
        count = len(datasplice) // 4  # Number of bytes to unpack (1 for char)

        unpacked_data = self.unpack_repeated_bytes(datasplice, 'f', count)
        RamanWavenumber = (1.0 / LaserExcitationWavelength - 1.0 / np.asarray(unpacked_data,
                                                                              dtype=np.float64)) * 1E7  # in 1/cm
        # print(RamanWavenumber)

        ###
        # Character Length of XML section = CLXML
        ###
        datasplice = contentTVBfile[0x1534:0x1538]
        # 'I': unsigned integer (4 byte)
        count = len(datasplice) // 4  # Number of bytes to unpack (1 for char)
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'I', count)

        CLXML = int(unpacked_data[0])
        # print(f'Character Length of XML section: {CLXML}')

        def ensure_list(obj):
            if isinstance(obj, list):
                return obj
            elif obj is None:
                return []
            else:
                return [obj]

        ###
        # XML part -> Date, LaserPower, Ramification Objective, Groove Density, Exposure_time, Number_Accumlations
        ###
        datasplice = contentTVBfile[0x1538:0x1538 + 1 * CLXML]
        # 'b': Signed char (1 byte)
        count = len(datasplice) // 1  # Number of bytes to unpack (1 for char)
        unpacked_data = self.unpack_repeated_bytes(datasplice, 'b', count)
        string_output_xml = ''.join(chr(b) for b in unpacked_data)
        # print(string_output_xml) # can be parsed with xmltodict
        xml_to_dic = xmltodict.parse(string_output_xml)
        xml_metadata_group = xml_to_dic['Info']['Groups']['Group']
        for group in xml_metadata_group:
            items_container = group.get('Items')
            if items_container and 'Item' in items_container:
                items = ensure_list(items_container['Item'])
                for item in items:
                    table['metadata'][item['Name']] = str(item['Value'])


        ###
        # List of Intensity counts for every frame in file
        ###
        offsetHeader = 0x1538 + 1 * CLXML + 3 * 4 + 8 + 101

        # Do this for every frame in file
        for frame in range(0, numFrames, 1):
            table = self.append_table(tables)
            # print(frame)
            table['metadata']['frame'] = str(frame)
            datasplice = contentTVBfile[offsetHeader:offsetHeader + 4 * NRWE]
            # 'f': float (4 byte)
            count = len(datasplice) // 4  # Number of bytes to unpack (1 for char)
            unpacked_data = self.unpack_repeated_bytes(datasplice, 'f', count)

            IntensityCount = np.asarray(unpacked_data, dtype=np.float64)
            # print(IntensityCount)

            offsetHeader += 4 * NRWE + 3 * 4 + 8 + 101  # specific after every frame
            columns = [RamanWavenumber, IntensityCount]
            table['rows'] = list(list(x) for x in zip(*columns))

        return tables


Readers.instance().register(TvbReader)