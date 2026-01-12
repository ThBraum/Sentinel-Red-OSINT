# syntax=docker/dockerfile:1

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.1.4

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-ansi --no-root

COPY . .

RUN mkdir -p /app/outputs

ENTRYPOINT ["python", "main.py"]
