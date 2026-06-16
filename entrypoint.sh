#!/bin/bash
set -e

if [ -n "$MODEL_URL" ]; then
  echo "Fetching model weights from MODEL_URL …"
  python download_model.py
fi

echo "Starting Flask dashboard on port ${PORT:-7860} …"
exec gunicorn flask_app:app -c gunicorn.conf.py
