import importlib.metadata
import os

os.environ["TYPEGUARD_DISABLE"] = "1"

TITLE = importlib.metadata.distribution('chemotion-converter-app').name
VERSION = importlib.metadata.version('chemotion-converter-app')

if __name__ == '__main__':
    print(f"{TITLE} version {VERSION}")
