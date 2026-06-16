"""Flask dashboard — run locally with: python flask_app.py"""
import os
from werkzeug.utils import secure_filename

from flask import Flask, jsonify, render_template, request, send_file

from detector import (
    RESULTS_DIR,
    analyze_image,
    bytes_to_bgr,
    get_model_status,
    load_model,
    preload_model,
    save_result_pair,
)
from opg_validator import NotOpgError, validate_opg
from samples import list_samples, sample_path, SAMPLES_DIR

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_BYTES = 20 * 1024 * 1024


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/status")
    def status():
        st = get_model_status()
        if not st["available"] and os.environ.get("MODEL_URL"):
            from download_model import ensure_model
            try:
                ensure_model()
            except Exception:
                pass
            st = get_model_status()
        if st["available"] and not st["loaded"] and not st["loading"]:
            preload_model()
            st = get_model_status()
        return jsonify(st)

    @app.route("/api/samples")
    def samples_list():
        items = []
        for name in list_samples():
            label = os.path.splitext(name)[0].replace("_", " ").replace("-", " ")
            items.append({
                "name": name,
                "label": label.title(),
                "url": f"/api/samples/{name}",
            })
        return jsonify({"samples": items, "count": len(items)})

    @app.route("/api/samples/<filename>")
    def samples_file(filename):
        path = sample_path(filename)
        if not path:
            return jsonify({"error": "Sample not found"}), 404
        return send_file(path)

    def _run_analysis(data, filename, confidence):
        img = bytes_to_bgr(data, filename)
        validate_opg(img)
        annotated, detections = analyze_image(img, confidence=confidence)
        stem = os.path.splitext(filename)[0] or "scan"
        orig_name, marked_name = save_result_pair(img, annotated, stem)
        return {
            "success": True,
            "detections": detections,
            "count": len(detections),
            "original_url": f"/api/result/{orig_name}",
            "marked_url": f"/api/result/{marked_name}",
            "download_url": f"/api/download/{marked_name}",
            "filename": marked_name,
        }

    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        try:
            confidence = float(request.form.get("confidence", 0.25))
            confidence = max(0.05, min(0.95, confidence))
        except ValueError:
            confidence = 0.25

        sample_name = request.form.get("sample", "").strip()

        try:
            if sample_name:
                path = sample_path(sample_name)
                if not path:
                    return jsonify({"error": "Sample not found"}), 404
                with open(path, "rb") as sf:
                    data = sf.read()
                filename = os.path.basename(path)
            else:
                if "file" not in request.files:
                    return jsonify({"error": "No file uploaded"}), 400
                f = request.files["file"]
                if not f.filename:
                    return jsonify({"error": "No file selected"}), 400
                filename = secure_filename(f.filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_EXT:
                    return jsonify({"error": "Use JPG, PNG, or PDF"}), 400
                data = f.read()
                if len(data) > MAX_BYTES:
                    return jsonify({"error": "File too large (max 20 MB)"}), 400

            return jsonify(_run_analysis(data, filename, confidence))
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 503
        except NotOpgError as exc:
            return jsonify({"error": str(exc), "code": "not_opg"}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"Analysis failed: {exc}"}), 500

    @app.route("/api/result/<filename>")
    def result_image(filename):
        safe = os.path.basename(filename)
        path = os.path.join(RESULTS_DIR, safe)
        if not os.path.isfile(path):
            return jsonify({"error": "Not found"}), 404
        return send_file(path, mimetype="image/jpeg")

    @app.route("/api/download/<filename>")
    def download(filename):
        safe = os.path.basename(filename)
        path = os.path.join(RESULTS_DIR, safe)
        if not os.path.isfile(path):
            return jsonify({"error": "Not found"}), 404
        return send_file(path, as_attachment=True, download_name=safe)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4005))
    print(f"OPG Flask dashboard -> http://localhost:{port}")
    status = get_model_status()
    if status["available"]:
        preload_model()
        print(f"  Model: {status['path']} (loading in background…)")
    else:
        print(f"  Warning: {status['error']}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
