import io
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, request
from flask_cors import CORS

from .converters import Converter
from .readers import registry
from .writers.jcamp import JcampWriter


def create_app(test_config=None):
    load_dotenv(Path().cwd() / '.env')

    logging.basicConfig(level=os.getenv('LOG_LEVEL'))

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        PROFILES_DIR=os.getenv('PROFILES_DIR', 'profiles'),
        CORS=os.getenv('CORS', 'False').lower() in ['true', 't', '1']
    )

    if app.config['CORS']:
        CORS(app)

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.route('/', methods=['GET'])
    def root():
        return make_response(jsonify({'status': 'ok'}), 200)

    # Step 1 (advanced): gets file, saves file im temp dir,
    # returns data from file as json
    @app.route('/api/v1/tables', methods=['POST'])
    def tables():
        if request.files.get('file'):
            file = request.files.get('file')
            file_reader = io.BufferedReader(file)
            reader = registry.match_reader(file_reader, file.filename, file.content_type)

            if reader:
                response_data = reader.process()
                return jsonify(response_data), 201
            else:
                return jsonify(
                    {'error': 'your file could not be processed'}), 400
        else:
            return jsonify({'error': 'please provide file'}), 400

    # Step 2 (advanced): get json that defines rules and identifiers for file
    # from step 1, saves rules and identifiers as profile returns jcamp
    @app.route('/api/v1/profiles', methods=['POST'])
    def profiles():
        data = json.loads(request.data)

        converter = Converter(**data)
        profile = converter.save_profile()

        return jsonify(profile), 201

    # Simple View: gets file, converts file, searches for profile,
    # return jcamp based on profile
    @app.route('/api/v1/conversions', methods=['POST'])
    def conversions():
        if request.files.get('file'):
            file = request.files.get('file')
            file_reader = io.BufferedReader(file)
            reader = registry.match_reader(file_reader, file.filename, file.content_type)

            if reader:
                file_data = reader.process()
                file_data_metadata = file_data.pop('metadata')

                converter = Converter.match_profile(file_data_metadata)
                if converter:
                    prepared_data = converter.apply_to_data(file_data.get('data'))

                    jcamp_buffer = io.StringIO()
                    jcamp_writer = JcampWriter(jcamp_buffer)
                    jcamp_writer.write(prepared_data)

                    return Response(
                        jcamp_buffer.getvalue(),
                        mimetype="chemical/x-jcamp-dx",
                        headers={
                            "Content-Disposition": "attachment;filename=test.jcamp"
                        })

            return jsonify({'error': 'your file could not be processed'}), 400
        else:
            return jsonify({'error': 'please provide file'}), 400

    return app
