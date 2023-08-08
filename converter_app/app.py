import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from .converters import Converter
from .datasets import Dataset
from .models import File, Profile
from .options import OPTIONS
from .readers import registry
from .utils import checkpw, human2bytes
from .writers.jcamp import JcampWriter
from .writers.jcampzip import JcampZipWriter


def create_app(test_config=None):
    load_dotenv(Path().cwd() / '.env')

    # setup logging
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(), filename=os.getenv('LOG_FILE'))

    # open (plain) htpasswd file for the clients
    def get_clients():
        htpasswd_path = os.getenv('HTPASSWD_PATH')
        if htpasswd_path:
            clients = {}
            with open(htpasswd_path) as fp:
                for line in fp.readlines():
                    username, password = line.strip().split(':')
                    clients[username] = password
        else:
            return None
        return clients

    # configure app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        PROFILES_DIR=os.getenv('PROFILES_DIR', 'profiles'),
        DATASETS_DIR=os.getenv('DATASETS_DIR', 'datasets'),
        MAX_CONTENT_LENGTH=human2bytes(os.getenv('MAX_CONTENT_LENGTH', '64M')),
        CORS=bool(os.getenv('CORS', False)),
        CLIENTS=get_clients() is not None
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
        if not app.config['CLIENTS']:
            return 'dev'
        else:
            hashed_password = get_clients().get(username)
            if hashed_password is not None:
                if checkpw(password.encode(), hashed_password.encode()):
                    return username

    # configure routes

    @app.route('/', methods=['GET'])
    def root():
        '''
        Utility endpoint: Just return ok
        '''
        return make_response(jsonify({'status': 'ok'}), 200)

    @app.route('/client', methods=['GET'])
    @auth.login_required
    def client():
        '''
        Utility endpoint: Return the client_id iflogged in
        '''
        return make_response(jsonify({'client_id': auth.current_user()}), 200)

    @app.route('/conversions', methods=['POST'])
    @auth.login_required
    def retrieve_conversion():
        '''
        Simple View: upload file, convert to table, search for profile,
        return jcamp based on profile
        '''
        client_id = auth.current_user()
        if request.files.get('file'):
            file = File(request.files.get('file'))
            reader = registry.match_reader(file)

            if reader:
                reader.process()
                converter = Converter.match_profile(client_id, reader.as_dict)

                if converter:
                    converter.process()

                    conversion_format = request.form.get('format', 'jcampzip')
                    if conversion_format == 'jcampzip':
                        writer = JcampZipWriter(converter)
                    elif conversion_format == 'jcamp':
                        if len(converter.tables) == 1:
                            writer = JcampWriter(converter)
                        else:
                            return jsonify({'error': 'Conversion to a single JCAMP file is not supported for this file.'}), 400
                    else:
                        return jsonify({'error': 'Conversion format is not supported.'}), 400

                    try:
                        writer.process()
                    except AssertionError:
                        return jsonify({'error': 'There was an error while converting your file.'}), 400

                    file_name = Path(file.name).with_suffix(writer.suffix)

                    response = Response(writer.write(), mimetype=writer.mimetype)
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
            file = File(request.files.get('file'))
            reader = registry.match_reader(file)

            if reader:
                reader.process()
                reader.validate()

                # only return the first 10 rows of each table
                for index, table in enumerate(reader.tables):
                    reader.tables[index]['rows'] = table['rows'][:10]

                return jsonify(reader.as_dict), 201
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
        profile = Profile(profile_data, client_id)
        if profile.clean():
            profile.save()
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
                profile.save()
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

    @app.route('/datasets', methods=['GET'])
    @auth.login_required
    def list_datasets():
        datasets = Dataset.list()
        return jsonify([dataset.dataset_data for dataset in datasets]), 200

    @app.route('/options', methods=['GET'])
    @auth.login_required
    def list_options():
        return jsonify(OPTIONS), 200

    return app
