"""Download best.pt at deploy time from GitHub Release or MODEL_URL env var."""
import os
import urllib.request

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(APP_DIR, "models", "best.pt"))
MODEL_URL = os.environ.get("MODEL_URL", "")


def ensure_model():
  os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
  if os.path.isfile(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1_000_000:
    print(f"Model OK: {MODEL_PATH} ({os.path.getsize(MODEL_PATH):,} bytes)")
    return True
  if not MODEL_URL:
    print("MODEL_URL not set — place best.pt in models/ manually")
    return os.path.isfile(MODEL_PATH)
  print(f"Downloading model from MODEL_URL …")
  urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
  size = os.path.getsize(MODEL_PATH)
  print(f"Downloaded {size:,} bytes")
  if size < 1_000_000:
    raise RuntimeError("Download failed — file too small (check MODEL_URL)")
  return True


if __name__ == "__main__":
  ensure_model()
