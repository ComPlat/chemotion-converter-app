import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS

from .converters import Converter
from .models import Profile
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
    def not_found(error=None):
        return make_response(jsonify({'error': 'Not found'}), 404)

    @app.route('/', methods=['GET'])
    def root():
        '''
        Utility endpoint: Just return ok
        '''
        return make_response(jsonify({'status': 'ok'}), 200)

    @app.route('/conversions', methods=['POST'])
    def retrieve_conversion():
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
                    try:
                        writer.process(converter_header, converter_data)
                    except AssertionError:
                        return jsonify({'error': 'There was an error while converting your file.'}), 400

                    file_name = Path(file.filename).with_suffix(writer.suffix)

                    response = Response(writer.write(), mimetype='chemical/x-jcamp-dx')
                    response.headers['Content-Disposition'] = 'attachment;filename={}'.format(file_name)
                    return response

            return jsonify({'error': 'Your file could not be processed.'}), 400
        else:
            return jsonify({'error': 'No file provided.'}), 400

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

                # only return the first 10 rows of each table
                for index, table in enumerate(response_json['data']):
                    response_json['data'][index]['rows'] = table['rows'][:10]

                response_json['options'] = JcampWriter().options
                return jsonify(response_json), 201
            else:
                return jsonify(
                    {'error': 'Your file could not be processed.'}), 400
        else:
            return jsonify({'error': 'No file provided.'}), 400

    @app.route('/profiles', methods=['GET'])
    def list_profiles():
        profiles = Profile.list()
        return jsonify([profile.as_dict for profile in profiles]), 200

    @app.route('/profiles', methods=['POST'])
    def create_profile():
        profile_data = json.loads(request.data)
        profile = Profile(profile_data)

        if profile.clean():
            profile.save()
            return jsonify(profile.as_dict), 201
        else:
            return jsonify(profile.errors), 400

    @app.route('/profiles/<profile_id>', methods=['GET'])
    def retrieve_profile(profile_id):
        profile = Profile.retrieve(profile_id)
        if profile:
            return jsonify(profile.as_dict), 200
        else:
            abort(404)

    @app.route('/profiles/<profile_id>', methods=['PUT'])
    def update_profile(profile_id):
        profile = Profile.retrieve(profile_id)
        if profile:
            try:
                profile.data = json.loads(request.data)
            except json.decoder.JSONDecodeError:
                return jsonify({'error': 'Bad request'}), 400

            if profile.clean():
                profile.save()
                return jsonify(profile.as_dict), 200
            else:
                return jsonify(profile.errors), 400
        else:
            abort(404)

    @app.route('/profiles/<profile_id>', methods=['DELETE'])
    def delete_profile(profile_id):
        profile = Profile.retrieve(profile_id)
        if profile:
            profile.delete()
            return '', 204
        else:
            abort(404)

    return app
