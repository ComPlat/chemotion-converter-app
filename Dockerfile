# pull official base image
FROM python:3.10.7-slim-buster



RUN apt-get update && apt-get install -y -q --no-install-recommends libmagic1 apache2-utils

RUN groupadd chemotion -g 2002
RUN useradd chemotion -u 2002 -g 2002 -c Chemotion -m -d /srv/chemotion -s /bin/bash



WORKDIR /srv/chemotion

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY requirements ./requirements
COPY .env.prod ./.env

# install dependencies
RUN pip install --upgrade pip

RUN mkdir /var/log/chemotion-converter
RUN mkdir /run/chemotion-converter

EXPOSE 9000

# USER chemotion
# installs the package in editable mode
RUN pip install -r requirements/common.txt

CMD ${GUNICORN_BIN} --bind converter:8000 "${FLASK_APP}:create_app()"

