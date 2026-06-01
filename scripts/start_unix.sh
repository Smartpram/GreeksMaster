#!/bin/bash
echo "Starting MyBreezeApp..."
cd "$(dirname "$0")"
export FLASK_APP=app.main:app
export FLASK_ENV=development
python3 -m flask run --host=0.0.0.0 --port=5000
