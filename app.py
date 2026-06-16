"""
Hugging Face Spaces entrypoint (Gradio).
HF runs this file by default — do not use the Flask dev server here.
Local Flask dashboard: python flask_app.py
"""
import os
import tempfile

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/Ultralytics")

import cv2
import gradio as gr

from detector import analyze_image, bytes_to_bgr, get_model_status, load_model
from download_model import ensure_model
from opg_validator import NotOpgError, validate_opg
from samples import list_samples

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_EXAMPLES = 6


def _resolve_file_path(file_obj):
    if file_obj is None:
        return None
    if isinstance(file_obj, str):
        return file_obj
    if isinstance(file_obj, list):
        if not file_obj:
            return None
        first = file_obj[0]
        return first if isinstance(first, str) else getattr(first, "name", None)
    return getattr(file_obj, "name", str(file_obj))


def _ensure_model_ready():
    if not get_model_status()["available"]:
        ensure_model()
    status = get_model_status()
    if not status["available"]:
        raise gr.Error(
            "Model weights not found. Set the MODEL_URL secret on this Space "
            "to your GitHub Release download link for best.pt."
        )
    load_model()
    status = get_model_status()
    if not status["loaded"]:
        raise gr.Error(status["error"] or "Model failed to load.")


def bgr_to_rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def analyze(file_obj, confidence):
    file_path = _resolve_file_path(file_obj)
    if not file_path:
        raise gr.Error("Please upload an OPG image (JPG/PNG) or PDF, or pick a sample below.")

    name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        data = f.read()

    try:
        _ensure_model_ready()
        img = bytes_to_bgr(data, name)
        validate_opg(img)
        annotated, detections = analyze_image(img, confidence=confidence)
    except NotOpgError as exc:
        raise gr.Error(str(exc)) from exc
    except RuntimeError as exc:
        raise gr.Error(str(exc)) from exc

    summary = f"**{len(detections)}** region(s) flagged"
    if detections:
        rows = "\n".join(
            f"- {d['label']} **{d['confidence'] * 100:.1f}%** — "
            f"box ({d['x1']},{d['y1']})→({d['x2']},{d['y2']})"
            for d in detections
        )
        summary += f"\n\n{rows}"
    else:
        summary += "\n\nNo faulty regions at this sensitivity."

    return bgr_to_rgb(img), bgr_to_rgb(annotated), summary


INTRO = """
### OPG Faulty Tooth Detection
Upload a **panoramic dental X-ray (OPG)** — JPG, PNG, or PDF.  
Or try a **sample scan** from the library below.  
YOLOv8 highlights suspect faulty regions. **Educational use only** — not a medical diagnosis.
"""

_sample_files = [
    os.path.join(APP_DIR, "images", name)
    for name in list_samples()[:MAX_EXAMPLES]
]
_example_inputs = [[p, 0.25] for p in _sample_files if os.path.isfile(p)]

with gr.Blocks(title="OPG Faulty Tooth Detection") as demo:
    gr.Markdown(INTRO)
    with gr.Row():
        with gr.Column():
            file_in = gr.File(label="OPG scan", file_types=[".jpg", ".jpeg", ".png", ".pdf"])
            conf = gr.Slider(0.05, 0.95, value=0.25, step=0.05, label="Detection sensitivity")
            btn = gr.Button("Analyze OPG", variant="primary")
            if _example_inputs:
                gr.Examples(
                    examples=_example_inputs,
                    inputs=[file_in, conf],
                    label="Sample library — click to load a demo OPG",
                )
        with gr.Column():
            out_orig = gr.Image(label="Original")
            out_marked = gr.Image(label="Marked result")
            out_text = gr.Markdown()

    btn.click(analyze, [file_in, conf], [out_orig, out_marked, out_text])

# Hugging Face runs app.py directly; Gradio 6 needs an explicit launch().
if os.getenv("SPACE_ID") or __name__ == "__main__":
    demo.launch()
