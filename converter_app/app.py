"""
The Chemotion-Converter is a versatile Python module designed
to streamline the process of converting data files into the
bagit container format, facilitating seamless integration
with the Chemotion platform. This module comes equipped with
a Flask server that exposes various endpoints, providing
users with the capability to effortlessly create profiles for the conversion process.
"""

import logging
import os
from pathlib import Path

import dotenv
import flask
from str2bool import str2bool

from converter_app.profile_migration.utils.registration import Migrations
from converter_app.router import get_clients, setup_flask_routing
from converter_app.utils import human2bytes
from converter_app.validation import validate_all_profiles


# Example usage


def create_app():
    """
    Creates a Flask server that exposes various endpoints, providing
    users with the capability to effortlessly create profiles for the conversion process.
    :return: Flask app
    """
    dotenv.load_dotenv(Path().cwd() / '.env')

    # setup logging
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                        filename=os.getenv('LOG_FILE'))

    # configure app
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        PROFILES_DIR=os.getenv('PROFILES_DIR', 'profiles'),
        DATASETS_DIR=os.getenv('DATASETS_DIR', 'datasets'),
        MAX_CONTENT_LENGTH=human2bytes(os.getenv('MAX_CONTENT_LENGTH', '64M')),
        CORS=str2bool(os.getenv('CORS', 'False').lower()),
        DEBUG=str2bool(os.getenv('DEBUG', 'False').lower()),
        CLIENTS=get_clients() is not None
    )

    os.makedirs(app.config['PROFILES_DIR'], exist_ok=True)
    Migrations().run_migration(app.config['PROFILES_DIR'])
    validate_all_profiles(app.config['PROFILES_DIR'])
    app.debug = app.config['DEBUG']
    setup_flask_routing(app)

    return app
