"""
The Chemotion-Converter is a versatile Python module designed
to streamline the process of converting data files into the
bagit container format, facilitating seamless integration
with the Chemotion platform. This module comes equipped with
a Flask server that exposes various endpoints, providing
users with the capability to effortlessly create profiles for the conversion process.
"""
import json
import os
from pathlib import Path

from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from converter_app.converters import Converter
from converter_app.datasets import Dataset
from converter_app.models import File, Profile
from converter_app.options import OPTIONS
from converter_app.readers import READERS as registry
from converter_app.utils import checkpw
from converter_app.writers.jcamp import JcampWriter
from converter_app.writers.jcampzip import JcampZipWriter
from profile_migration.utils.registration import Migrations


def get_clients() -> dict[str:str] | None:
    """
    opens (plain) htpasswd file for the clients. Generates dict
    with username->password
    :return: Dict with username->password
    """
    htpasswd_path = os.getenv('HTPASSWD_PATH')
    if htpasswd_path:
        clients = {}
        with open(htpasswd_path, encoding='utf8') as fp:
            for line in fp.readlines():
                username, password = line.strip().split(':')
                clients[username] = password
    else:
        return None
    return clients


def error_router(app: Flask):
    """
    Equips flask app with error handler

    :param app: Flask app
    """

    # configure errorhandler
    @app.errorhandler(404)
    def not_found(_: None):
        return make_response(jsonify({'error': 'Not found'}), 404)


def auth_router(app: Flask) -> HTTPBasicAuth:
    """
    Equips flask app with error handler

    :param app: Flask app
    :return: basic Auth model
    """
    # configure basic auth
    auth = HTTPBasicAuth()

    @auth.verify_password
    def verify_password(username, password):
        if not app.config['CLIENTS']:
            return 'dev'
        hashed_password = get_clients().get(username)
        if hashed_password is not None:
            if checkpw(password.encode(), hashed_password.encode()):
                return username
        return None

    return auth


def converting_router(app: Flask, auth: HTTPBasicAuth):
    """
    Equips flask app with all necessary entrypoints for file converting

    :param app: Flask app
    :param auth: Flask HTTPBasicAuth
    """

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
        return jcamp based on profiledescription
        '''
        client_id = auth.current_user()
        error_msg = 'No file provided.'
        if request.files.get('file'):
            file = File(request.files.get('file'))
            reader = registry.match_reader(file)
            error_msg = 'Your file could not be processed. No Reader available!'

            if reader:
                reader.process()
                converter = Converter.match_profile(client_id, reader.as_dict)

                return _run_conversion(converter, file)
        return jsonify({'error': error_msg}), 400

    def _run_conversion(converter, file):
        if converter:
            converter.process()

            conversion_format = request.form.get('format', 'jcampzip')
            if conversion_format == 'jcampzip':
                writer = JcampZipWriter(converter)
            elif conversion_format == 'jcamp':
                if len(converter.tables) == 1:
                    writer = JcampWriter(converter)
                else:
                    return jsonify({
                        'error':
                            'Conversion to a single JCAMP file is not supported for this file.'
                    }), 400
            else:
                return jsonify({'error': 'Conversion format is not supported.'}), 400
            try:
                writer.process()
            except AssertionError:
                return jsonify({'error': 'There was an error while converting your file.'}), 400

            file_name = Path(file.name).with_suffix(writer.suffix)

            response = Response(writer.write(), mimetype=writer.mimetype)
            response.headers['Content-Disposition'] = f'attachment;filename={file_name}'
            return response
        return jsonify({'error': 'Your file could not be processed. No Profile available!'}), 400

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
            return jsonify(
                {'error': 'Your file could not be processed.'}), 400
        return jsonify({'error': 'No file provided.'}), 400


def profile_router(app: Flask, auth: HTTPBasicAuth):
    """
    Equips flask app with all necessary entrypoints for managing the converter profiles

    :param app: Flask app
    :param auth: Flask HTTPBasicAuth
    """

    @app.route('/profiles', methods=['GET'])
    @auth.login_required
    def list_profiles():
        client_id = auth.current_user()
        profiles = Profile.list_including_default(client_id)
        return jsonify([profile.as_dict for profile in profiles]), 200

    @app.route('/profiles', methods=['POST'])
    @auth.login_required
    def create_profile():
        client_id = auth.current_user()
        profile_data = json.loads(request.data)
        profile = Profile(profile_data, client_id)
        if profile.clean():
            Migrations().migrate_profile(profile)
            profile.save()
            return jsonify(profile.as_dict), 201
        return jsonify(profile.errors), 400

    @app.route('/profiles/<profile_id>', methods=['GET'])
    @auth.login_required
    def retrieve_profile(profile_id):
        client_id = auth.current_user()
        profile = Profile.retrieve(client_id, profile_id)
        if profile:
            return jsonify(profile.as_dict), 200
        abort(404)
        return None

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
                Migrations().migrate_profile(profile)
                profile.save()
                return jsonify(profile.as_dict), 200
            return jsonify(profile.errors), 400
        abort(404)
        return None

    @app.route('/profiles/<profile_id>', methods=['DELETE'])
    @auth.login_required
    def delete_profile(profile_id):
        client_id = auth.current_user()
        profile = Profile.retrieve(client_id, profile_id)
        if profile:
            profile.delete()
            return '', 204
        abort(404)
        return None


def utils_router(app: Flask, auth: HTTPBasicAuth):
    """
    Equips flask app with all necessary entrypoints for getting datasets and options

    :param app: Flask app
    :param auth: Flask HTTPBasicAuth
    """

    @app.route('/datasets', methods=['GET'])
    @auth.login_required
    def list_datasets():
        datasets = Dataset.list()
        return jsonify([dataset.dataset_data for dataset in datasets]), 200

    @app.route('/options', methods=['GET'])
    @auth.login_required
    def list_options():
        return jsonify(OPTIONS), 200


def setup_flask_routing(app: Flask):
    """
    Equips flask app with all necessary entrypoints

    :param app: Flask app
    """
    if app.config['CORS']:
        CORS(app, expose_headers=['Content-Disposition'])

    error_router(app)
    auth = auth_router(app)
    converting_router(app, auth)
    profile_router(app, auth)
    utils_router(app, auth)
