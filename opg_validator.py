"""Heuristic checks — is this image likely a panoramic dental OPG?"""
import cv2
import numpy as np


class NotOpgError(ValueError):
    """Raised when uploaded media does not look like an OPG scan."""


def validate_opg(img_bgr):
    """
    Score panoramic layout, grayscale X-ray appearance, and tonal range.
    Returns (ok, details_dict). Raises NotOpgError when validation fails.
    """
    h, w = img_bgr.shape[:2]
    if min(h, w) < 180:
        raise NotOpgError(
            "Image is too small to analyse. Please upload a full-resolution OPG scan."
        )

    ratio = max(w, h) / min(w, h)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    mean_sat = float(np.mean(hsv[:, :, 1]))
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))

    b, g, r = cv2.split(img_bgr.astype(np.float32))
    channel_dev = float(np.mean(np.abs(r - g) + np.abs(g - b) + np.abs(r - b)) / 3)
    rel_dev = channel_dev / (mean_val + 1e-6)

    scores = {
        "panoramic": ratio >= 1.28,
        "grayscale": rel_dev < 0.14 or mean_sat < 52,
        "xray_tone": 18 <= mean_val <= 215 and std_val >= 12,
    }
    passed = sum(scores.values())

    details = {
        "aspect_ratio": round(ratio, 2),
        "mean_saturation": round(mean_sat, 1),
        "grayscale_score": round(rel_dev, 3),
        "checks": scores,
    }

    if passed >= 2:
        return True, details

    reasons = []
    if not scores["panoramic"]:
        reasons.append(
            f"expected a wide panoramic layout (aspect ratio ≥ 1.28, got {ratio:.2f})"
        )
    if not scores["grayscale"]:
        reasons.append(
            "file looks like a colour photograph — OPG scans are grayscale X-rays"
        )
    if not scores["xray_tone"]:
        reasons.append(
            "brightness/contrast does not match a typical dental radiograph"
        )

    hint = (
        "This does not appear to be an orthopantomogram (OPG). "
        "Please upload a panoramic dental X-ray — wide grayscale radiograph showing the full jaw and teeth. "
        "Selfies, documents, and regular photos are not supported."
    )
    if reasons:
        hint += " Detected: " + "; ".join(reasons) + "."

    raise NotOpgError(hint)
