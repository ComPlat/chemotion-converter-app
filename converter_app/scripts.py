import argparse
import json
import logging
import os
import sys

from .writers.jcamp import JcampWriter

logging.basicConfig(level=os.getenv('LOG_LEVEL'))


def converter():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name')

    args = parser.parse_args()

    with open(args.file_name) as f:
        data = json.loads(f.read())

    logging.info(data)

    JcampWriter(sys.stdout).write(data)
