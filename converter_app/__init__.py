import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

__title__ = 'chemotion-converter-app'
__version__ = '0.1.0'
__author__ = 'Nicole Jung'
__email__ = 'nicole.jung(at)kit.edu'
__license__ = 'AGPL-3.0'
__copyright__ = 'Copyright (c) 2020 Karlsruhe Institute for Technology (KIT)'

VERSION = __version__


def create_app(test_config=None):
    load_dotenv(Path().cwd() / '.env')

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY')
    )

    CORS(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.route('/', methods=['GET'])
    def root():
        return make_response(jsonify({'status': 'ok'}), 200)

    return app
