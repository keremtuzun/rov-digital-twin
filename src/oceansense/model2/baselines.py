"""Deterministic, non-trained smoke baselines for Twin 2 D0 tensors."""

from __future__ import annotations

import numpy as np

BASELINE_NAMES = ("last_observation", "simple_heuristic")
FALLBACK_VALUE = 0.0
BASELINE_CONTRACTS = {
    "last_observation": {
        "definition": "Carry the most recent observed node estimate; use zero before first evidence.",
        "mapping": {
            "corrosion_probability": "corrosion",
            "crack_probability": "crack",
            "material_loss_probability": "material_loss",
            "fatigue_probability": "fatigue",
            "severity_estimate": "condition",
        },
        "confidence_use": "not_used",
        "neighbor_use": False,
        "fallback_value": FALLBACK_VALUE,
    },
    "simple_heuristic": {
        "definition": "Confidence-weight observed node-local proxies, then carry the latest estimate.",
        "mapping": {
            "primitive_states": "confidence*probability + (1-confidence)*severity_estimate",
            "condition": "confidence*severity_estimate + (1-confidence)*mean(probabilities)",
        },
        "confidence_use": "deterministic_observation_weight",
        "neighbor_use": False,
        "fallback_value": FALLBACK_VALUE,
    },
}


def _validate_inputs(observations: np.ndarray, mask: np.ndarray) -> None:
    if observations.ndim != 4 or observations.shape[-1] != 6:
        raise ValueError("observations must have shape [scenario,timestep,node,6]")
    if mask.shape != observations.shape[:3]:
        raise ValueError("mask must match observation scenario/timestep/node axes")
    if not set(np.unique(mask).tolist()).issubset({0, 1, False, True}):
        raise ValueError("mask values must be boolean or 0/1")


def _carry_forward(mapped: np.ndarray, mask: np.ndarray) -> np.ndarray:
    predictions = np.full((*mask.shape, 5), FALLBACK_VALUE, dtype=np.float32)
    for scenario in range(mask.shape[0]):
        last = np.full((mask.shape[2], 5), FALLBACK_VALUE, dtype=np.float32)
        for timestep in range(mask.shape[1]):
            observed = mask[scenario, timestep].astype(bool)
            last[observed] = mapped[scenario, timestep, observed]
            predictions[scenario, timestep] = last
    return predictions


def last_observation_predictions(observations: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Carry the latest explicit proxy-to-state mapping; use zero before first evidence."""
    _validate_inputs(observations, mask)
    mapped = np.concatenate((observations[..., :4], observations[..., 4:5]), axis=-1)
    return _carry_forward(mapped.astype(np.float32), mask)


def simple_heuristic_predictions(observations: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Confidence-weight observed proxies, then carry the latest node-local estimate."""
    _validate_inputs(observations, mask)
    probabilities = observations[..., :4]
    severity = observations[..., 4:5]
    confidence = observations[..., 5:6]
    primitive = confidence * probabilities + (1.0 - confidence) * severity
    condition = confidence * severity + (1.0 - confidence) * probabilities.mean(
        axis=-1, keepdims=True
    )
    mapped = np.concatenate((primitive, condition), axis=-1)
    return _carry_forward(np.clip(mapped, 0.0, 1.0).astype(np.float32), mask)


def predict(baseline_name: str, observations: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if baseline_name == "last_observation":
        return last_observation_predictions(observations, mask)
    if baseline_name == "simple_heuristic":
        return simple_heuristic_predictions(observations, mask)
    raise ValueError(f"unknown baseline: {baseline_name}")
