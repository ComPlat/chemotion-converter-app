import importlib.metadata

DIST_NAME = 'chemotion-converter-app'

TITLE = importlib.metadata.distribution(DIST_NAME).name
VERSION = importlib.metadata.version(DIST_NAME)
