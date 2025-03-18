# syntax=docker/dockerfile:1

FROM python:3.12.3-slim

RUN apt-get update && apt-get install -y -q --no-install-recommends libmagic1 apache2-utils git nginx build-essential curl
RUN pip install wheel setuptools pip pybind11 gunicorn --upgrade

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash


RUN mkdir /srv/converter

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /srv/converter

COPY ./etc_doc/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

CMD bash ./entrypoint.sh