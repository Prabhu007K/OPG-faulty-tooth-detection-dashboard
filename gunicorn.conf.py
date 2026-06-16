import os

# ONE worker only — each Gunicorn worker loads full PyTorch + YOLO (~400–600 MB RAM each).
# Multiple workers = out-of-memory on Render Free/Starter (512 MB).
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
threads = 2
timeout = 120
preload_app = False
max_requests = 500
max_requests_jitter = 50
