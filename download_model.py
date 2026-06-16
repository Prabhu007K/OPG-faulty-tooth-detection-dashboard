"""Download best.pt at deploy time from GitHub Release or MODEL_URL env var."""
import os
import sys
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
        print("ERROR: models/best.pt not found and MODEL_URL secret is not set.")
        print("Fix: HF Space → Settings → Secrets → add MODEL_URL = GitHub Release link")
        print("Or upload best.pt manually to the models/ folder in Space Files.")
        return False
    print(f"Downloading model from MODEL_URL …")
    try:
        req = urllib.request.Request(
            MODEL_URL,
            headers={"User-Agent": "opg-faulty-tooth-detection/1.0"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = resp.read()
    except Exception as exc:
        print(f"ERROR: MODEL_URL download failed: {exc}")
        raise
    with open(MODEL_PATH, "wb") as out:
        out.write(data)
    size = os.path.getsize(MODEL_PATH)
    print(f"Downloaded {size:,} bytes → {MODEL_PATH}")
    if size < 1_000_000:
        os.remove(MODEL_PATH)
        raise RuntimeError(
            "MODEL_URL download failed — file too small (got HTML, not best.pt). "
            "Use the direct link ending in /best.pt, e.g. "
            "https://github.com/USER/REPO/releases/download/v1.0/best.pt"
        )
    return True


if __name__ == "__main__":
    ok = ensure_model()
    if not ok:
        sys.exit(1)
