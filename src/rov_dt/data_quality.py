"""Streaming telemetry freshness, jitter, missingness and plausibility checks."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FieldQuality:
    field: str
    age_s: float
    sampling_rate_hz: float
    missing_rate: float
    jitter_s: float
    saturated: bool
    finite: bool
    plausible: bool
    stale: bool
    usable: bool
    reasons: tuple[str, ...]


def assess_field_quality(
    field: str,
    timestamps: Iterable[float],
    values: Iterable[float | None],
    *,
    now_s: float,
    stale_after_s: float,
    plausible_range: tuple[float, float] | None = None,
    saturation_range: tuple[float, float] | None = None,
) -> FieldQuality:
    times = list(timestamps)
    samples = list(values)
    if len(times) != len(samples) or not times:
        raise ValueError("timestamps and values must be non-empty and aligned")
    pairs = sorted(zip(times, samples), key=lambda pair: pair[0])
    intervals = [right[0] - left[0] for left, right in zip(pairs, pairs[1:]) if right[0] > left[0]]
    sampling_rate = 1.0 / statistics.fmean(intervals) if intervals else 0.0
    jitter = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
    present = [value for _, value in pairs if value is not None]
    missing_rate = 1.0 - len(present) / len(pairs)
    last_time = max(time for time, value in pairs if value is not None) if present else -math.inf
    age = now_s - last_time if math.isfinite(last_time) else math.inf
    finite = bool(present) and all(math.isfinite(float(value)) for value in present)
    plausible = finite and (
        plausible_range is None
        or all(plausible_range[0] <= float(value) <= plausible_range[1] for value in present)
    )
    saturated = bool(present) and saturation_range is not None and any(
        float(value) <= saturation_range[0] or float(value) >= saturation_range[1]
        for value in present
    )
    stale = age > stale_after_s
    reasons = []
    if missing_rate > 0:
        reasons.append("missing_samples")
    if not finite:
        reasons.append("nan_or_infinite")
    if not plausible:
        reasons.append("implausible")
    if saturated:
        reasons.append("saturated")
    if stale:
        reasons.append("stale")
    usable = finite and plausible and not stale and missing_rate < 0.5
    return FieldQuality(
        field, age, sampling_rate, missing_rate, jitter, saturated, finite, plausible, stale, usable, tuple(reasons)
    )


class DataQualityMonitor:
    """Bounded per-field history for online quality checks."""

    def __init__(self, history_size: int = 100):
        if history_size < 2:
            raise ValueError("history_size must be at least two")
        self.history_size = history_size
        self._timestamps: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=history_size))
        self._values: dict[str, deque[float | None]] = defaultdict(lambda: deque(maxlen=history_size))

    def update(self, timestamp_s: float, fields: dict[str, float | None]) -> None:
        for name, value in fields.items():
            self._timestamps[name].append(float(timestamp_s))
            self._values[name].append(value)

    def assess(
        self,
        field: str,
        *,
        now_s: float,
        stale_after_s: float,
        plausible_range: tuple[float, float] | None = None,
        saturation_range: tuple[float, float] | None = None,
    ) -> FieldQuality:
        if field not in self._timestamps:
            raise KeyError(field)
        return assess_field_quality(
            field,
            self._timestamps[field],
            self._values[field],
            now_s=now_s,
            stale_after_s=stale_after_s,
            plausible_range=plausible_range,
            saturation_range=saturation_range,
        )
