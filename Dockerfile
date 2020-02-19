FROM python:alpine

ARG REPOSITORY_URL=https://github.com/beralt/horepg.git
ENV REPOSITORY_SOURCE_URL=${REPOSITORY_URL}

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh

RUN git clone ${REPOSITORY_SOURCE_URL} /horepg
WORKDIR /horepg

RUN python setup.py install
RUN chown -R root:root docker/entrypoint.sh
RUN chmod 755 docker/entrypoint.sh

ENTRYPOINT docker/entrypoint.sh