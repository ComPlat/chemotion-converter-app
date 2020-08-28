chemotion-converter-app
=======================

Development setup
-----------------

First, ensure that basic Python development prerequisites are installed on the system. For Debian or Ubuntu this can be done using:

```bash
apt-get install build-essential python3-dev python3-pip python3-venv
```

After cloning the repository, we recommend to create a [virtual environment](https://docs.python.org/3/tutorial/venv.html) for the application:

```bash
python3 -m venv env
source env/bin/activate  # this needs to be done in each new terminal session
```

Then, the application and its dependencies can be installed:

```bash
pip install -e .                     # installs the package in editable mode
pip install -r requirements/dev.txt  # only needed for the development setup
```

The application is configured using environment variables, which can be read from a `.env` file. The file `.env.sample` as template. At least `FLASK_APP=converter_app.app` needs to be set.

The Flask development server can be started now:

```bash
flask run
```

Production setup
----------------

For the production deployment, we recommend to create a dedicated user:

```
groupadd chemotion -g 2002
useradd chemotion -u 2002 -g 2002 -c Chemotion -m -d /srv/chemotion -s /bin/bash
```

Again we create a virtual environment, but now we install the application directly from GitHub:

```bash
python3 -m venv env
source env/bin/activate
pip install git+https://github.com/ComPlat/converter-app
```

The development server is not suited for a production deployment. Instead we recomend to use a reverse-proxy setup using [gunicorn](https://gunicorn.org/) and [NGINX](https://www.nginx.com/).

First create a systemd service file in `/etc/systemd/system/chemotion-converter-app.service`:

```
# /etc/systemd/system/chemotion-converter-app.service
[Unit]
Description=chemotion-converter-app gunicorn daemon
After=network.target

[Service]
User=chemotion
Group=chemotion
WorkingDirectory=/srv/chemotion

Environment=FLASK_APP=converter_app.app
Environment=FLASK_ENV=production
Environment=LOG_LEVEL=INFO
Environment=LOG_FILE=/var/log/chemotion/converter-app.log
Environment=PROFILES_DIR=/srv/chemotion/profiles

ExecStart=/srv/chemotion/env/bin/gunicorn --workers 3  \
                                          --bind localhost:9000 \
                                          --timeout 60 \
                                          "converter_app.app:create_app()"

[Install]
WantedBy=multi-user.target
```

Reload systemd using `systemctl daemon-reload` and start the service:

```bash
systemctl start chemotion-converter-app
systemctl enable chemotion-converter-app
```

The guincorn server listens on port 9000 on localhost. Using the following code in your NGINX configuration it can be reversed proxied to the `/api/v1` route:

```nginx
    location /api/v1 {
        proxy_pass         http://127.0.0.1:9000/;
        proxy_redirect     off;

        proxy_set_header   Host                 $host;
        proxy_set_header   X-Real-IP            $remote_addr;
        proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    $scheme;
    }
```
