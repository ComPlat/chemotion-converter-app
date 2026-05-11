service nginx start

export FLASK_APP=converter_app.app
export FLASK_ENV=production
export PROFILES_DIR=/var/share/profiles
export DATASETS_DIR=/var/share/datasets
export HTPASSWD_PATH=/var/share/htpasswd/htpasswd
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/converter/application.log
export GUNICORN_BIN=/srv/converter/env/bin/gunicorn
export GUNICORN_WORKER=3
export GUNICORN_PORT=8000
export GUNICORN_TIMEOUT=500
export GUNICORN_PID_FILE=/run/chemotion-converter/pid
export GUNICORN_ACCESS_LOG_FILE=/var/log/converter/access.log
export GUNICORN_ERROR_LOG_FILE=/var/log/converter/error.log
export MAX_CONTENT_LENGTH=250G

gunicorn --bind 0.0.0.0:8000 "converter_app.app:create_app()" --timeout 500



