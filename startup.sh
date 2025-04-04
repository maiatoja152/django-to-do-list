#!/bin/bash

uv run manage.py migrate
uv run manage.py collectstatic --noinput

uv run gunicorn --bind 0.0.0.0:8000 config.wsgi:application