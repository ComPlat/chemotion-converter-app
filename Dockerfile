# syntax=docker/dockerfile:1

FROM python:3.10.7-slim-buster

RUN apt-get update && apt-get install -y -q --no-install-recommends libmagic1 apache2-utils
RUN mkdir /srv/chemotion
WORKDIR /srv/chemotion

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .
RUN pip3 install -r requirements/dev.txt

RUN mkdir /var/log/chemotion-converter



RUN rm -f ./.env

RUN mv ./.env.doc ./.env

RUN mkdir /run/chemotion-converter

EXPOSE 8000

# USER chemotion
# installs the package in editable mode
RUN pip install -r requirements/common.txt

CMD gunicorn --bind converter:8000 "converter_app.app:create_app()"

