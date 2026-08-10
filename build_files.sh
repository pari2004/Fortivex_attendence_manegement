#!/bin/bash
set -e

python3 -m venv /tmp/build-venv
source /tmp/build-venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
