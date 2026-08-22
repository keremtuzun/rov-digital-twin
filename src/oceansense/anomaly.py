from __future__ import annotations

from .schemas import Anomaly, Classification


def score_anomaly(classification: Classification) -> Anomaly:
    """Apply the documented v1 anomaly rule without implying confirmed damage."""
    normal_labels = {"ok", "normal_surface", "structure_ok", "healthy_coral", "healthy_seafloor", "normal_water_condition", "suitable_habitat_indicator"}
    score = 1.0 - classification.confidence if classification.label in normal_labels else classification.confidence
    score = max(0.0, min(1.0, score))
    level = "low" if score < 0.40 else ("medium" if score < 0.70 else "high")
    if classification.label in normal_labels:
        reason = "Normal surface prediction; residual uncertainty is treated as anomaly evidence."
    else:
        reason = f"Model predicted {classification.label} with {classification.confidence:.2f} confidence."
    return Anomaly(round(score, 6), level, reason)
