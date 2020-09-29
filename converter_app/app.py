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

    if os.getenv('LOG_FILE'):
        logging.basicConfig(level=os.getenv('LOG_LEVEL'), filename=os.getenv('LOG_FILE'))
    else:
        logging.basicConfig(level=os.getenv('LOG_LEVEL'))

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        PROFILES_DIR=os.getenv('PROFILES_DIR', 'profiles'),
        CORS=os.getenv('CORS', 'False').lower() in ['true', 't', '1']
    )

    if app.config['CORS']:
        CORS(app, expose_headers=['Content-Disposition'])

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.route('/', methods=['GET'])
    def root():
        '''
        Utility endpoint: Just return ok
        '''
        return make_response(jsonify({'status': 'ok'}), 200)

    @app.route('/profiles', methods=['GET'])
    def list_profiles():
        '''
        Utility endpoint: List all profiles
        '''
        profiles = Converter.list_profiles()
        return jsonify(profiles), 200

    @app.route('/tables', methods=['POST'])
    def retrieve_table():
        '''
        Step 1 (advanced): upload file and convert to table
        '''
        if request.files.get('file'):
            file = request.files.get('file')
            reader = registry.match_reader(file, file.filename, file.content_type)

            if reader:
                response_json = reader.process()
                response_json['options'] = JcampWriter().options
                return jsonify(response_json), 201
            else:
                return jsonify(
                    {'error': 'Your file could not be processed.'}), 400
        else:
            return jsonify({'error': 'No file provided.'}), 400

    @app.route('/profiles', methods=['POST'])
    def create_profile():
        '''
        Step 2 (advanced): upload json that defines rules and identifiers for file
        from step 1, saves rules and identifiers as profile
        '''

        profile_json = json.loads(request.data)

        converter = Converter(profile_json)
        errors = converter.clean()

        if errors:
            return jsonify(errors), 400
        else:
            converter.save()
            return jsonify(converter.profile), 201

    @app.route('/conversions', methods=['POST'])
    def create_conversion():
        '''
        Simple View: upload file, convert to table, search for profile,
        return jcamp based on profile
        '''
        if request.files.get('file'):
            file = request.files.get('file')
            reader = registry.match_reader(file, file.filename, file.content_type)

            if reader:
                file_json = reader.process()
                converter = Converter.match_profile(file_json)
                if converter:
                    converter_header = converter.get_header()
                    converter_data = converter.get_data(file_json.get('data'))

                    writer = JcampWriter()
                    writer.process(converter_header, converter_data)

                    file_name = Path(file.filename).with_suffix(writer.suffix)

                    response = Response(writer.write(), mimetype='chemical/x-jcamp-dx')
                    response.headers['Content-Disposition'] = 'attachment;filename={}'.format(file_name)
                    return response

            return jsonify({'error': 'Your file could not be processed.'}), 400
        else:
            return jsonify({'error': 'No file provided.'}), 400

    return app
