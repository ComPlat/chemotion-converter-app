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

The application is configured using environment variables, which can be read from a `.env` file. The file `.env.dev` can be used as template. At least `FLASK_APP=converter_app.app` needs to be set.

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

In production, HTTP basic auth is used to seperate clients. First, create a `htpasswd` file using the `sha1` hashing algorithm:

```bash
htpasswd -s -c htpasswd client  # create a new file with the client_id "client"
htpasswd -s htpasswd client     # update an existing file for the client_id "client"
```

The path to this file needs to be provided in `.env` as `HTPASSWD_PATH`.

The development server is not suited for a production deployment. Instead we recomend to use a reverse-proxy setup using [gunicorn](https://gunicorn.org/) and [NGINX](https://www.nginx.com/).

Create the `.env` file in `/srv/chemotion/.env`, but use `.env.prod` as template, since it contains the variables we need to set for gunicorn.

In order to create the needed `log` and `run` directories create a `tmpfiles.d` config in `/etc/tmpfiles.d/chemotion-converter.conf`. A sample file can be found in [etc/tmpfiles.d/chemotion-converter.conf](etc/tmpfiles.d/chemotion-converter.conf). Create the directories using:

```
systemd-tmpfiles --create
```

Next, create a systemd service file in `/etc/systemd/system/chemotion-converter.service`. Again, a sample file can be found in [etc/systemd/system/chemotion-converter.service](etc/systemd/system/chemotion-converter.service). Reload systemd and start (and enable) the service:

```bash
systemctl daemon-reload
systemctl start chemotion-converter
systemctl enable chemotion-converter
```

If the service won't start, `journalctl -xf` might indicate what is wrong.

The guincorn server listens on the port given in the env file (default: 9000) on localhost. Using the following code in your NGINX configuration, it can be reversed proxied to the `/api/v1` route:

```nginx
    location /api/v1 {
        proxy_pass         http://127.0.0.1:9000/;
        proxy_redirect     off;

        proxy_set_header   Host                 $host;
        proxy_set_header   X-Real-IP            $remote_addr;
        proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    $scheme;
    }

    client_max_body_size 64M;  # set this to the maximum file size allowed for upload
```


## Acknowledgments

This project has been funded by the **[DFG]**.

[![DFG Logo]][DFG]


Funded by the [Deutsche Forschungsgemeinschaft (DFG, German Research Foundation)](https://www.dfg.de/) under the [National Research Data Infrastructure – NFDI4Chem](https://nfdi4chem.de/) – Projektnummer **441958208** since 2020.


[DFG]: https://www.dfg.de/en/
[DFG Logo]: https://www.dfg.de/zentralablage/bilder/service/logos_corporate_design/logo_negativ_267.png
