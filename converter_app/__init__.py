import json
import os
import tempfile
from io import StringIO
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, request
from flask_cors import CORS

from .converters import match_profile
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
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY')
    )

    CORS(app)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

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

    # Step 1 (advanced): gets file, saves file im temp dir,
    # returns data from file as json
    @app.route('/api/v1/fileviewer', methods=['POST'])
    def return_file_data_as_json():
        if request.files.get('file'):
            file = request.files.get('file')
            reader = registry.match_reader(file)
            if reader:
                return jsonify(reader.process()), 201
            else:
                return jsonify(
                    {'error': 'your file could not be processed'}), 400
        else:
            return jsonify({'error': 'please provide file'}), 400

    # Step 2 (advanced): get json that defines rules and identifiers for file
    # from step 1, saves rules and identifiers as profile returns jcamp
    @app.route('/api/v1/createprofile', methods=['POST'])
    def convert_json():
        from .writers.jcamp import JcampWriter
        from .converters.base import Converter

        data = json.loads(request.data)
        uuid = data.pop('uuid')
        converter = Converter(**data)
        converter.save_profile()

        json_path = os.path.join(
            tempfile.gettempdir(), '{}.json'.format(uuid))

        with open(json_path, 'r') as data_file:
            data_dict = json.load(data_file)
            header = data_dict['header']
            data = data_dict['data']
            prepared_data = converter.apply_to_data(header, data)

            jcamp_buffer = StringIO()
            jcamp_writer = JcampWriter(jcamp_buffer)
            jcamp_writer.write(prepared_data)

            return Response(
                jcamp_buffer.getvalue(),
                mimetype="chemical/x-jcamp-dx",
                headers={
                    "Content-Disposition": "attachment;filename=test.jcamp"
                })

    # Simple View: gets file, converts file, searches for profile,
    # return jcamp based on profile
    @app.route('/api/v1/simplefileconversion', methods=['POST'])
    def return_jcamp_from_fileuplaod_from_identifier():
        from .writers.jcamp import JcampWriter
        if request.files.get('file'):
            file = request.files.get('file')
            reader = registry.match_reader(file)
            if reader:
                file_data = reader.process()
                file_data_metadata = file_data.pop('metadata')
                converter = match_profile(file_data_metadata)
                prepared_data = converter.apply_to_data(**file_data)

                jcamp_buffer = StringIO()
                jcamp_writer = JcampWriter(jcamp_buffer)
                jcamp_writer.write(prepared_data)

                return Response(
                    jcamp_buffer.getvalue(),
                    mimetype="chemical/x-jcamp-dx",
                    headers={
                        "Content-Disposition": "attachment;filename=test.jcamp"
                    })
            else:
                return jsonify(
                    {'error': 'your file could not be processed'}), 400
        else:
            return jsonify({'error': 'please provide file'}), 400

    return app
