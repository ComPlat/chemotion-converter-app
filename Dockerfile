FROM python:3.12.3-slim
LABEL authors="martin"


RUN apt-get update && apt-get install -y -q --no-install-recommends libmagic1 apache2-utils git nginx build-essential curl
RUN pip install wheel setuptools pip pybind11 gunicorn --upgrade

RUN mkdir /srv/converter

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /srv/converter

COPY ./etc_doc/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

RUN rm /etc/nginx/sites-available/default
RUN rm /etc/nginx/sites-enabled/default


RUN ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

COPY ./requirements ./requirements

COPY ./etc_doc/nginx/sites-available/default /etc/nginx/sites-available/default
RUN chmod 644 /etc/nginx/sites-available/default

RUN pip install -r requirements/dev.txt

COPY . .

RUN mkdir /var/log/converter
RUN mkdir /var/share
RUN mkdir /var/share/profiles
RUN mkdir /var/share/datasets
RUN mkdir /var/share/htpasswd

CMD bash ./entrypoint.sh