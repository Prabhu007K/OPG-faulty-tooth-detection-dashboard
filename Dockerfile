FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=7860
ENV YOLO_CONFIG_DIR=/tmp/Ultralytics
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

# Inline startup — avoids Windows CRLF issues with entrypoint.sh uploads
CMD bash -c 'mkdir -p models && if [ ! -f models/best.pt ]; then if [ -n "$MODEL_URL" ]; then python download_model.py || exit 1; else echo "WARNING: No models/best.pt and MODEL_URL not set"; fi; else echo "Model file already present: models/best.pt"; fi && echo "Starting Flask on port ${PORT:-7860} …" && exec gunicorn flask_app:app -c gunicorn.conf.py'
