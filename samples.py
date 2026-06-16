"""Sample OPG images from the images/ library folder."""
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(APP_DIR, "images")
SAMPLE_EXT = {".jpg", ".jpeg", ".png"}


def list_samples():
    if not os.path.isdir(SAMPLES_DIR):
        return []
    out = []
    for name in sorted(os.listdir(SAMPLES_DIR)):
        if name.startswith("."):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in SAMPLE_EXT:
            out.append(name)
    return out


def sample_path(filename):
    from werkzeug.utils import secure_filename
    safe = secure_filename(filename)
    path = os.path.join(SAMPLES_DIR, safe)
    if not os.path.isfile(path):
        return None
    return path
