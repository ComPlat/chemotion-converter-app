# Private variables, not passed in from outside, but helpful for this file
ARG BASE=ubuntu:22.04
ARG TINI_VERSION="v0.19.0"

# Stage 1: the base image
FROM ${BASE} AS base

# set timezone
ARG TZ=Europe/Berlin
RUN ln -s /usr/share/zoneinfo/${TZ} /etc/localtime

# locales
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8
RUN echo "LANG=${LANG}" >/etc/locale.conf && \
    echo "LC_ALL=${LANG}" >>/etc/locale.conf && \
    echo "${LANG} UTF-8" >/etc/locale.gen

# install system packages
RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install -y --no-install-recommends --autoremove --fix-missing locales && \
    apt-get clean && \
    locale-gen en_US.UTF-8

# install tini and yq
ARG TINI_VERSION
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
ADD https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 /bin/yq
RUN chmod +x /bin/yq && chmod +x /tini

FROM scratch AS converter-base
COPY --from=base / /

# Stage 1: prepare the converter image
RUN apt-get update && \
    apt-get install -y --no-install-recommends --autoremove --fix-missing python3-pip python3-venv libmagic1 curl git

WORKDIR /srv
RUN git clone --single-branch --branch dev-deploy-1 --depth=1 https://github.com/ComPlat/chemotion-converter-app chemotion

WORKDIR /srv/chemotion
RUN python3 -m venv env && . env/bin/activate && \
    pip install --no-cache-dir -r /srv/chemotion/requirements/common.txt

RUN test -f "/srv/chemotion/.env.prod" && mv "/srv/chemotion/.env.prod" "/srv/chemotion/.env" && mkdir -p /var/log/chemotion-converter/ && chmod a+wrx /var/log/chemotion-converter/

ADD https://github.com/ptrxyz/chemotion/raw/refs/heads/v180rc4/converter/pass /bin/genpass
RUN chmod +x /bin/genpass && echo "$(/bin/genpass chemotion chemotion)" > /srv/chemotion/htpasswd   # use echo to append newline.

ENV PATH=/srv/chemotion/env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    VIRTUAL_ENV=/srv/chemotion/env       \
    MAX_CONTENT_LENGTH=250M              \
    GUNICORN_TIMEOUT=180                 \
    PROFILES_DIR=/srv/chemotion/profiles \
    DATASETS_DIR=/srv/chemotion/datasets \
    HTPASSWD_PATH=/srv/chemotion/htpasswd

RUN apt-get remove -y git && apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Stage 4: finalize the image
FROM converter-base AS app

EXPOSE 4000

WORKDIR /srv/chemotion
CMD ["gunicorn", "--bind", "0.0.0.0:4000", "converter_app.app:create_app()", "--preload"]

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:4000/

LABEL \
    "org.opencontainers.image.authors"="Chemotion Team" \
    "org.opencontainers.image.title"="Chemotion Converter" \
    "org.opencontainers.image.description"="Image for Chemotion Converter" \
    "chemotion.internal.service.id"="converter"