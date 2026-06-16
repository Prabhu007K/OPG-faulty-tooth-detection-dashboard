# Deployment guide (fresh start)

Render **Free (512 MB)** often crashes with YOLO + PyTorch.  
**Recommended: Hugging Face Spaces** — free, built for ML, enough RAM.

---

## Part 1 — GitHub (clean upload)

### Create repo
1. GitHub → **New repository** → name: `opg-faulty-tooth-detection`
2. Public repo

### Upload these files/folders

```
app.py              # Gradio — Hugging Face runs this by default
flask_app.py        # Flask dashboard — local only
hf_app.py           # alias (optional)
detector.py
opg_validator.py
download_model.py
run.py
gunicorn.conf.py
requirements.txt
start.bat
.gitignore
README.md
description.txt
DEPLOY.md
templates/
static/
models/README.md
```

### Optional (large — skip if upload fails)
- `dataset-training.ipynb`
- `fork-of-kaggle.ipynb`

### Do NOT upload
- `models/best.pt` (use GitHub Release instead)
- `uploads/`, `results/`, `__pycache__/`, `.venv/`

### GitHub Release (model weights)
1. Repo → **Releases** → **Create new release**
2. Tag: `v1.0`
3. Attach **`best.pt`** (~50 MB)
4. Publish
5. Copy download URL:
   ```
   https://github.com/YOUR_USER/opg-faulty-tooth-detection/releases/download/v1.0/best.pt
   ```

### Repo description
Paste text from `description.txt` into GitHub **Description** field.

---

## Part 2 — Deploy on Hugging Face Spaces (recommended)

### Why HF instead of Render Free?
| | Render Free | Hugging Face Spaces |
|--|-------------|---------------------|
| RAM | 512 MB (OOM with YOLO) | ~16 GB on free CPU tier |
| ML apps | Often fails | Designed for this |
| Cost | Free (unstable for YOLO) | Free |

### Steps
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **Create new Space**
2. Settings:
   - **Space name:** `opg-faulty-tooth-detection` (or your choice)
   - **License:** MIT
   - **SDK:** **Gradio**
   - **Hardware:** **CPU basic** (free)
   - **Visibility:** Public
3. **Connect GitHub repo** (same repo from Part 1)  
   OR upload files manually to the Space repo
4. In Space → **Settings** → **SDK:** Gradio · **App file:** `app.py` (default)
5. In Space → **Settings** → **Secrets** → add:

   | Name | Value |
   |------|--------|
   | `MODEL_URL` | Your GitHub Release URL for `best.pt` |

6. Space will run `pip install -r requirements.txt` and start Gradio from `app.py`
7. First build takes **5–10 minutes** (downloads PyTorch CPU)
8. Live URL:
   ```
   https://huggingface.co/spaces/YOUR_USERNAME/opg-faulty-tooth-detection
   ```

### Verify
- Open the Space URL
- Upload an OPG image → **Analyze OPG**
- Marked image should appear

Put this URL in your portfolio README **Live Demo** section.

---

## Part 3 — Local demo (always works)

```bash
pip install -r requirements.txt
# Copy best.pt to models/
python flask_app.py
```

Open **http://localhost:4005** — full Flask dashboard.

---

## Part 4 — Render (only if you pay for RAM)

Render **Free/Starter (512 MB)** is **not recommended** for this app.

If you still use Render:
- **Instance:** Standard (**2 GB RAM**) minimum
- **Build command:**
  ```bash
  pip install -r requirements.txt && python download_model.py
  ```
- **Start command:**
  ```bash
  gunicorn flask_app:app -c gunicorn.conf.py
  ```
- **Environment variable:**
  | Key | Value |
  |-----|--------|
  | `MODEL_URL` | GitHub Release URL for best.pt |

---

## Part 5 — What NOT to use

| Platform | Why |
|----------|-----|
| **Netlify** | Static only — no Python/YOLO |
| **GitHub Pages** | Static only |
| **Render Free** | Out of memory with YOLO |

---

## Quick decision

```
Portfolio live demo  →  Hugging Face Spaces (app.py = Gradio)
Full custom UI       →  Local Flask (flask_app.py) or Render Standard ($)
GitHub               →  Code + Release for best.pt
```
