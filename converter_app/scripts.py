import argparse
import logging
import mimetypes
import os

from .readers import registry
from .writers.jcamp import JcampWriter

logging.basicConfig(level=os.getenv('LOG_LEVEL'))


def converter():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name')

    args = parser.parse_args()

    with open(args.file_name, 'rb') as file:
        reader = registry.match_reader(file, args.file_name, mimetypes.guess_type(args.file_name))

        if reader:
            data = reader.process()
            logging.info(data)

    # JcampWriter(sys.stdout).write(data)
    # else:
    #     parser.error('no Reader found')
