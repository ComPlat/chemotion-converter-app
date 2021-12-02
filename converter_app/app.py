import json
import logging
from pathlib import Path
import yaml

from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from .converters import Converter
from .models import Profile
from .readers import registry
from .writers.jcamp import JcampWriter
from .utils import human2bytes


def create_app(test_config=None):
    # read config from yaml file
    config = yaml.safe_load(Path().cwd().joinpath('config.yml').read_text())

    # setup logging
    logging.basicConfig(level=config.get('log_level', 'INFO').upper(), filename=config.get('log_file'))

    # configure app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=config.get('secret_key'),
        PROFILES_DIR=config.get('profiles_dir', 'profiles'),
        MAX_CONTENT_LENGTH=human2bytes(config.get('max_content_length', '64M')),
        CORS=bool(config.get('cors', False))
    )

    # configure CORS
    if app.config['CORS']:
        CORS(app, expose_headers=['Content-Disposition'])

    # configure errorhandler
    @app.errorhandler(404)
    def not_found(error=None):
        return make_response(jsonify({'error': 'Not found'}), 404)

    # configure basic auth
    auth = HTTPBasicAuth()

    @auth.verify_password
    def verify_password(username, password):
        for client in config.get('clients', []):
            if client.get('client_id') == username and client.get('client_secret') == password:
                return client.get('client_id')
        return False

    # configure routes

    @app.route('/', methods=['GET'])
    def root():
        '''
        Utility endpoint: Just return ok
        '''
        return make_response(jsonify({'status': 'ok'}), 200)

    @app.route('/conversions', methods=['POST'])
    @auth.login_required
    def retrieve_conversion():
        '''
        Simple View: upload file, convert to table, search for profile,
        return jcamp based on profile
        '''
        client_id = auth.current_user()
        if request.files.get('file'):
            file = request.files.get('file')
            reader = registry.match_reader(file, file.filename, file.content_type)

            if reader:
                file_json = reader.process()
                converter = Converter.match_profile(client_id, file_json)

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
    @auth.login_required
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
    @auth.login_required
    def list_profiles():
        client_id = auth.current_user()
        profiles = Profile.list(client_id)
        return jsonify([profile.as_dict for profile in profiles]), 200

    @app.route('/profiles', methods=['POST'])
    @auth.login_required
    def create_profile():
        client_id = auth.current_user()
        profile_data = json.loads(request.data)
        profile = Profile(profile_data)

        if profile.clean():
            profile.save(client_id)
            return jsonify(profile.as_dict), 201
        else:
            return jsonify(profile.errors), 400

    @app.route('/profiles/<profile_id>', methods=['GET'])
    @auth.login_required
    def retrieve_profile(profile_id):
        client_id = auth.current_user()
        profile = Profile.retrieve(client_id, profile_id)
        if profile:
            return jsonify(profile.as_dict), 200
        else:
            abort(404)

    @app.route('/profiles/<profile_id>', methods=['PUT'])
    @auth.login_required
    def update_profile(profile_id):
        client_id = auth.current_user()
        profile = Profile.retrieve(client_id, profile_id)
        if profile:
            try:
                profile.data = json.loads(request.data)
            except json.decoder.JSONDecodeError:
                return jsonify({'error': 'Bad request'}), 400

            if profile.clean():
                profile.save(client_id)
                return jsonify(profile.as_dict), 200
            else:
                return jsonify(profile.errors), 400
        else:
            abort(404)

    @app.route('/profiles/<profile_id>', methods=['DELETE'])
    @auth.login_required
    def delete_profile(profile_id):
        client_id = auth.current_user()
        profile = Profile.retrieve(client_id, profile_id)
        if profile:
            profile.delete()
            return '', 204
        else:
            abort(404)

    return app
