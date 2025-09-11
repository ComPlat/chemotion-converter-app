import base64
import hashlib
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import git

from converter_app.writers.jcamp import JcampWriter
from converter_app.writers.jcampzip import JcampZipWriter
from converter_app.writers.rdf import RDFWriter


def human2bytes(string):
    """
    Bytes size converter
    :param string: input unit string for example 100kb
    """
    if not string:
        return 0

    m = re.match(r'([0-9.]+)\s*([A-Za-z]+)', string)
    number, unit = float(m.group(1)), m.group(2).strip().lower()

    if unit in ['kb', 'k']:
        number = number * 1000
    elif unit in ['mb', 'm']:
        number = number * 1000**2
    elif unit in ['gb', 'g']:
        number = number * 1000**3
    elif unit in ['tb', 't']:
        number = number * 1000**4
    elif unit in ['pb', 'p']:
        number = number * 1000**5
    elif unit == 'kib':
        number = number * 1024
    elif unit == 'mib':
        number = number * 1024**2
    elif unit == 'gib':
        number = number * 1024**3
    elif unit == 'tib':
        number = number * 1024**4
    elif unit == 'pib':
        number = number * 1024**5
    return number


def check_uuid(string):
    """
    :param string: uuid string
    :return: True if string is a uuid
    """
    try:
        return uuid.UUID(string, version=4)
    except ValueError:
        return False


def checkpw(password, hashed_password):
    """
    :param password: Password string
    :param hashed_password: hashed password in htaccess
    :return: True if password is correct
    """
    m = hashlib.sha1()
    m.update(password)
    return (b'{SHA}' + base64.b64encode(m.digest())) == hashed_password

def run_conversion(converter, conversion_format):
    if converter:
        converter.process()
        if conversion_format == 'jcampzip':
            writer = JcampZipWriter(converter)
        elif conversion_format == 'rdf':
            writer = RDFWriter(converter)
        elif conversion_format == 'jcamp':
            if len(converter.tables) == 1:
                writer = JcampWriter(converter)
            else:
                raise ValueError('Conversion to a single JCAMP file is not supported for this file.')
        else:
            raise ValueError('Conversion format is not supported.')

        writer.process()
        return writer

    raise ValueError('Your file could not be processed. No Profile available!')


def load_public_profiles(profiles: Optional[str|Path] = None, data_files: Optional[str|Path] = None):


    with tempfile.TemporaryDirectory() as t:
        # Clone into temporary dir
        git.Repo.clone_from('https://github.com/ComPlat/chemotion_saurus.git', t, branch='added_data_files', depth=1)

        if profiles:
            os.makedirs(os.path.dirname(profiles), exist_ok=True)
            shutil.move(os.path.join(t, 'static/files/shared_ChemConverter_files/profiles'), profiles)
        if data_files:
            os.makedirs(os.path.dirname(data_files), exist_ok=True)
            shutil.move(os.path.join(t, 'static/files/shared_ChemConverter_files/data_files'), data_files)
