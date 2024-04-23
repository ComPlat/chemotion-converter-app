"""
This module manages all registered reader. As main interface surfs readers.helper.Readers.instance() or readers.READERS
"""
import importlib
import logging
import os

from converter_app.readers.helper.reader import Readers

for module in os.listdir(os.path.dirname(__file__)):
    if module != '__init__.py' and module[-3:] == '.py':
        importlib.import_module(f'converter_app.readers.{module[:-3]}')

logger = logging.getLogger(__name__)

READERS = Readers.instance()
all_reader = [x for x, _ in READERS.readers.items()]
logger.info('All reader: %s', ", ".join(all_reader))
