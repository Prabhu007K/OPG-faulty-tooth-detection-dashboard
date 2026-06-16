"""YOLO inference + annotation for OPG / image uploads."""
import os
import threading
import uuid
from datetime import datetime

import cv2
import numpy as np

APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(APP_DIR, ".ultralytics"))
MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(APP_DIR, "models", "best.pt"))
RESULTS_DIR = os.path.join(APP_DIR, "results")
UPLOADS_DIR = os.path.join(APP_DIR, "uploads")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

_model = None
_model_error = None
_model_loading = False
_load_lock = threading.Lock()

YELLOW_BGR = (0, 255, 255)
LABEL_BG = (0, 200, 200)


def get_model_status():
    exists = os.path.isfile(MODEL_PATH)
    if _model is not None:
        return {
            "loaded": True,
            "loading": False,
            "available": exists,
            "path": MODEL_PATH,
            "error": None,
        }
    if _model_loading:
        return {
            "loaded": False,
            "loading": True,
            "available": exists,
            "path": MODEL_PATH,
            "error": None,
        }
    if exists:
        return {
            "loaded": False,
            "loading": False,
            "available": True,
            "path": MODEL_PATH,
            "error": _model_error,
        }
    return {
        "loaded": False,
        "loading": False,
        "available": False,
        "path": MODEL_PATH,
        "error": "Model weights not found. Place best.pt in the models/ folder.",
    }


def load_model():
    """Load YOLO weights (blocking). Use preload_model() at startup when possible."""
    global _model, _model_error, _model_loading

    if _model is not None:
        return _model

    with _load_lock:
        if _model is not None:
            return _model
        if not os.path.isfile(MODEL_PATH):
            _model_error = f"Missing model file: {MODEL_PATH}"
            return None
        size = os.path.getsize(MODEL_PATH)
        if size < 1_000_000:
            _model_error = (
                f"Model file invalid ({size:,} bytes). "
                "Build likely downloaded an HTML page instead of best.pt — "
                "use gdown for Google Drive (see README)."
            )
            return None
        _model_loading = True
        try:
            os.environ.setdefault("OMP_NUM_THREADS", "1")
            os.environ.setdefault("MKL_NUM_THREADS", "1")
            from ultralytics import YOLO
            _model = YOLO(MODEL_PATH)
            _model_error = None
            return _model
        except Exception as exc:
            _model_error = str(exc)
            return None
        finally:
            _model_loading = False


def preload_model():
    """Start loading the model in a background thread (non-blocking)."""
    if _model is not None or _model_loading or not os.path.isfile(MODEL_PATH):
        return

    def _worker():
        load_model()

    threading.Thread(target=_worker, daemon=True).start()


def pdf_to_bgr(pdf_bytes):
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.page_count == 0:
        raise ValueError("PDF has no pages")
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img


def bytes_to_bgr(data, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return pdf_to_bgr(data)
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image file")
    return img


def draw_detections(img, boxes, names):
    annotated = img.copy()
    detections = []
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        label_name = names.get(cls_id, names[cls_id] if cls_id < len(names) else "faulty")
        label = f"{label_name} {conf:.0%}"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), YELLOW_BGR, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), LABEL_BG, -1)
        cv2.putText(annotated, label, (x1 + 2, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        detections.append({
            "label": label_name,
            "confidence": round(conf, 4),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "width": x2 - x1,
            "height": y2 - y1,
        })
    return annotated, detections


def analyze_image(img, confidence=0.25):
    model = load_model()
    if model is None:
        raise RuntimeError(_model_error or "Model not loaded")

    results = model.predict(img, conf=confidence, verbose=False, device="cpu")
    result = results[0]
    names = model.names if isinstance(model.names, dict) else {i: n for i, n in enumerate(model.names)}
    annotated, detections = draw_detections(img, result.boxes, names)
    return annotated, detections


def save_result_pair(original_bgr, annotated_bgr, stem):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    base = f"{stem}_{ts}_{uid}"
    orig_name = f"{base}_original.jpg"
    marked_name = f"{base}_marked.jpg"
    orig_path = os.path.join(RESULTS_DIR, orig_name)
    marked_path = os.path.join(RESULTS_DIR, marked_name)
    cv2.imwrite(orig_path, original_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    cv2.imwrite(marked_path, annotated_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    return orig_name, marked_name
