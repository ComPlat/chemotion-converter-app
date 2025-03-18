
clone_repo () {
  LOCALREPO_VC_DIR=$3/.git
  if [ ! -d "$LOCALREPO_VC_DIR" ]
  then
      git clone -b $2 "$1" "$3"
  else
      cd "$3"
      git reset --hard
      git pull $REPOSRC
      cd ..
  fi
}




REPO=https://github.com/ComPlat/chemotion-converter-client.git
LOCALREPO=/srv/converter/chemotion-converter-client

clone_repo $REPO master $LOCALREPO


cd "$LOCALREPO"

source /root/.bashrc



nvm install
npm install
nvm use
CONVERTER_APP_URL=${CONVERTER_URL}/api/v1 npm run build:prod
rm -r /var/www/html
mv public /var/www/html


REPO=https://github.com/ComPlat/chemotion-converter-app.git
LOCALREPO=/srv/converter/chemotion-converter-app
clone_repo $REPO dev $LOCALREPO

cd "$LOCALREPO"

rm /etc/nginx/sites-available/default
rm /etc/nginx/sites-enabled/default
cp ./etc_doc/nginx/sites-available/default /etc/nginx/sites-available/default
chmod 644 /etc/nginx/sites-available/default
ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

service nginx start


mkdir /var/log/converter
touch /var/log/converter/application.log
touch /var/log/converter/access.log
touch /var/log/converter/error.log

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
export GUNICORN_TIMEOUT=$TIMEOUT
export GUNICORN_PID_FILE=/run/chemotion-converter/pid
export GUNICORN_ACCESS_LOG_FILE=/var/log/converter/access.log
export GUNICORN_ERROR_LOG_FILE=/var/log/converter/error.log
export MAX_CONTENT_LENGTH=250G

pip install -r requirements/dev.txt
# tail -f /dev/null
gunicorn --bind 0.0.0.0:8000 "converter_app.app:create_app()" --timeout $TIMEOUT



