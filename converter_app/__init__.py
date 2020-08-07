import json
import os
import tempfile
from io import StringIO
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, request
from flask_cors import CORS

from .readers import registry

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

    @app.route('/api/v1/fileconversion', methods=['POST'])
    def convert_file():
        if request.files.get('file'):
            file = request.files.get('file')
            reader = registry.match_reader(file)
            if reader:
                return reader.process()
            else:
                return jsonify(
                    {'error': 'your file could not be processed'}), 400
        else:
            return jsonify({'error': 'please provide file'}), 200

    @app.route('/api/v1/jcampconversion', methods=['POST'])
    def convert_json():
        from .writers.jcamp import JcampWriter

        form = request.form
        x_column = form['x_column']
        y_column = form['y_column']
        time_stamp = form['time_stamp']
        first_row_is_header = False if form['firstRowIsHeader'] == 'false' else True

        json_path = os.path.join(
            tempfile.gettempdir(), '{}.json'.format(time_stamp))

        with open(json_path, 'r') as data_file:
            data_dict = json.load(data_file)
            points = []

            if not first_row_is_header:
                x = None
                y = None
                for entry in data_dict['header']:
                    if entry['key'] == x_column:
                        x = entry['name']
                    if entry['key'] == y_column:
                        y = entry['name']
                if x and y:
                    points.append([x, y])

            for row in data_dict['data']:
                x_value = row.get(x_column)
                y_value = row.get(y_column)
                points.append([x_value, y_value])

            prepared_data = {
                'points': points
            }

            jcamp_buffer = StringIO()
            jcamp_writer = JcampWriter(jcamp_buffer)
            jcamp_writer.write(prepared_data)

            return Response(
                jcamp_buffer.getvalue(),
                mimetype="chemical/x-jcamp-dx",
                headers={
                    "Content-Disposition": "attachment;filename=test.jcamp"
                })
    return app
