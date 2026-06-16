"""Production entrypoint — Render / Railway."""
import os
from flask_app import app
from detector import get_model_status, preload_model

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4005))
    status = get_model_status()
    if status["available"]:
        preload_model()
    app.run(host="0.0.0.0", port=port)
