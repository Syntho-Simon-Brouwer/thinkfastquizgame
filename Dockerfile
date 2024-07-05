FROM python:3.12-alpine as BUILDER
WORKDIR /app/

RUN apk add curl
# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false
COPY . /app/
RUN poetry install --no-root --only main

ENV PYTHONPATH=/app

