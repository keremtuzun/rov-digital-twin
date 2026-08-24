"""Image quality and classifier uncertainty checks for failure-first perception."""

from __future__ import annotations

import math
from pathlib import Path


def image_quality_score(path: str | Path) -> dict[str, float]:
    from PIL import Image, ImageFilter, ImageStat

    with Image.open(path) as source:
        image = source.convert("L")
        stats = ImageStat.Stat(image)
        brightness = stats.mean[0] / 255.0
        contrast = min(1.0, stats.stddev[0] / 64.0)
        edges = image.filter(ImageFilter.FIND_EDGES)
        sharpness = min(1.0, ImageStat.Stat(edges).mean[0] / 32.0)
    exposure = max(0.0, 1.0 - abs(brightness - 0.5) * 2.0)
    quality = 0.35 * exposure + 0.35 * contrast + 0.30 * sharpness
    return {"quality": quality, "brightness": brightness, "contrast": contrast, "sharpness": sharpness}


def vision_uncertainty(probabilities: list[float], quality: float) -> dict[str, float | bool]:
    total = sum(probabilities)
    normalized = [value / total for value in probabilities]
    ordered = sorted(normalized, reverse=True)
    entropy = -sum(value * math.log(max(value, 1e-12)) for value in normalized) / math.log(len(normalized))
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]
    unknown = ordered[0] < 0.5 or entropy > 0.75 or margin < 0.12 or quality < 0.25
    return {"entropy": entropy, "top1_top2_margin": margin, "image_quality": quality, "unknown": unknown}
