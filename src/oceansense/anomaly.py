from __future__ import annotations

from .schemas import Anomaly, Classification


def score_anomaly(classification: Classification) -> Anomaly:
    """Apply the documented v1 anomaly rule without implying confirmed damage."""
    score = 1.0 - classification.confidence if classification.label == "normal_surface" else classification.confidence
    score = max(0.0, min(1.0, score))
    level = "low" if score < 0.40 else ("medium" if score < 0.70 else "high")
    if classification.label == "normal_surface":
        reason = "Normal surface prediction; residual uncertainty is treated as anomaly evidence."
    else:
        reason = f"Model predicted {classification.label} with {classification.confidence:.2f} confidence."
    return Anomaly(round(score, 6), level, reason)
