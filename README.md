# OPG Faulty Tooth Detection Dashboard

Upload orthopantomogram (OPG) dental X-rays, validate format, run YOLOv8 inference, and download annotated results. Includes a Flask dashboard (local) and a **Hugging Face Spaces** deploy path for a free public demo.

## Live Demo

<!-- Hugging Face Spaces — recommended -->
`https://huggingface.co/spaces/YOUR_USERNAME/opg-faulty-tooth-detection`

> **Deploy guide:** see **[DEPLOY.md](DEPLOY.md)** for step-by-step GitHub + Hugging Face setup.

## Where to deploy

| Platform | Recommended? | Notes |
|----------|--------------|--------|
| **Hugging Face Spaces** | **Yes (best free option)** | Gradio via `app.py` (default on HF) |
| **Local (`python flask_app.py`)** | Yes | Full custom UI on port 4005 |
| **Render Free** | **No** | 512 MB → memory exceeded with PyTorch |
| **Render Standard (2 GB)** | Optional | Paid; use `app.py` + `gunicorn.conf.py` |
| **Netlify / GitHub Pages** | No | Static only — no Python inference |

## Features

- OPG upload (JPG, PNG, PDF) with format validation
- **Sample library** — try demo OPGs from the `images/` folder (one-click on Flask UI)
- YOLOv8 faulty-region detection with yellow bounding boxes
- Adjustable confidence slider
- Side-by-side original vs marked result
- Download annotated image
- Flask dashboard + Gradio Space entrypoint

## Tech Stack

Python 3 · Flask · Gradio · Ultralytics YOLOv8 · OpenCV · PyMuPDF · CPU-only PyTorch

## Project Structure

```
├── app.py              # Gradio — Hugging Face Spaces (public demo)
├── flask_app.py        # Flask dashboard (local / paid cloud)
├── hf_app.py           # alias → app.py
├── detector.py         # YOLO inference
├── opg_validator.py    # OPG format checks
├── download_model.py   # Fetch best.pt from MODEL_URL at deploy
├── gunicorn.conf.py    # 1 worker only (if using Render paid)
├── requirements.txt
├── DEPLOY.md           # Full deployment walkthrough
├── models/best.pt      # local only — use GitHub Release for cloud
├── images/             # sample OPG scans for demo library (JPG/PNG)
├── templates/ + static/
└── dataset-training.ipynb
```

## Run Locally

```bash
pip install -r requirements.txt
# Copy best.pt → models/best.pt
python flask_app.py
```

Open **http://localhost:4005**

Add panoramic X-ray JPG/PNG files to **`images/`** to populate the sample library (see `images/README.md`).

## Model weights (cloud)

Do **not** commit `best.pt` to git. Instead:

1. Upload `best.pt` to a **GitHub Release** (tag `v1.0`)
2. Set secret **`MODEL_URL`** on Hugging Face to the release download link

See **[DEPLOY.md](DEPLOY.md)** for full instructions.

## Ethics

Educational use only — not a medical diagnosis. Consult a licensed dentist or radiologist.
