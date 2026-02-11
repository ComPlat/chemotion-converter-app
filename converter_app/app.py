"""
The Chemotion-Converter is a versatile Python module designed
to streamline the process of converting data files into the
bagit container format, facilitating seamless integration
with the Chemotion platform. This module comes equipped with
a Flask server that exposes various endpoints, providing
users with the capability to effortlessly create profiles for the conversion process.
"""
import importlib.metadata
import logging
import os
import uuid
from pathlib import Path

import dotenv
import flask
from str2bool import str2bool

from converter_app.profile_migration.utils.registration import Migrations
from converter_app.router import get_clients, setup_flask_routing
from converter_app.utils import human2bytes, cli_home_path
from converter_app.validation import validate_all_profiles
from converter_app.rdf import refresh_rdf_summery
from converter_app.models import Profile


# Example usage


def create_app(is_local_cli = False) -> flask.Flask:
    """
    Creates a Flask server that exposes various endpoints, providing
    users with the capability to effortlessly create profiles for the conversion process.
    :return: Flask app
    """
    if is_local_cli:
        os.environ['SECRET_KEY'] = uuid.uuid4().__str__()
        os.environ['PROFILES_DIR'] = Profile.cli_profiles_dir.__str__()
        os.environ['DATASETS_DIR'] = cli_home_path().joinpath('datasets').__str__()
        os.environ['CORS'] = 'False'
        os.environ['DEBUG'] = 'False'
        os.environ['IS_CLI'] = '1'
        os.environ['LOG_FILE'] = Path(os.getcwd()).joinpath('converter_app.log').__str__()
    else:
        dotenv.load_dotenv(Path().cwd() / '.env')
    rdf_json_path = refresh_rdf_summery()

    # setup logging
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                        filename=os.getenv('LOG_FILE'))

    # configure app
    debug = str2bool(os.getenv('DEBUG', 'False').lower())
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        PROFILES_DIR=os.getenv('PROFILES_DIR', 'profiles'),
        DATASETS_DIR=os.getenv('DATASETS_DIR', 'datasets'),
        MAX_CONTENT_LENGTH=human2bytes(os.getenv('MAX_CONTENT_LENGTH', '64M')),
        CORS=str2bool(os.getenv('CORS', 'False').lower()),
        DEBUG=debug,
        CLIENTS=get_clients() is not None,
        RDF_JSON=rdf_json_path,
        VERSION=importlib.metadata.version('chemotion-converter-app')
    )

    os.makedirs(app.config['PROFILES_DIR'], exist_ok=True)
    Migrations().run_migration(app.config['PROFILES_DIR'])
    validate_all_profiles(app.config['PROFILES_DIR'])
    app.debug = debug
    setup_flask_routing(app)

    return app
