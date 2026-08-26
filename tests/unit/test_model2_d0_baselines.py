import inspect
import json
from pathlib import Path

import numpy as np
import pytest

from oceansense.model2 import evaluation
from oceansense.model2.baselines import (
    last_observation_predictions,
    simple_heuristic_predictions,
)
from oceansense.model2.evaluation import (
    evaluate_baseline,
    load_d0_release,
    run_d0_smoke_evaluation,
)

ROOT = Path(__file__).resolve().parents[2]
D0 = ROOT / "data/model2/d0_debug"


def _small_inputs():
    observations = np.zeros((1, 3, 1, 6), dtype=np.float32)
    observations[0, 1, 0] = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
    mask = np.asarray([[[0], [1], [0]]], dtype=np.uint8)
    return observations, mask


def test_d0_loading_validates_and_has_expected_shapes():
    dataset = load_d0_release(D0)
    assert dataset.states.shape == (25, 4, 10, 5)
    assert dataset.observations.shape == (25, 4, 10, 6)
    assert dataset.observation_mask.shape == (25, 4, 10)
    assert dataset.manifest["approved_for_model_training"] is False


def test_release_validation_is_called_before_loading(monkeypatch):
    calls = []

    def reject_release(path, *, require_debug_d0):
        calls.append((Path(path), require_debug_d0))
        return {"valid": False, "errors": ["fixture rejection"]}

    monkeypatch.setattr(evaluation, "validate_release", reject_release)
    with pytest.raises(ValueError, match="validation failed"):
        load_d0_release(D0)
    assert calls == [(D0, True)]


def test_baseline_interfaces_cannot_receive_hidden_states():
    assert tuple(inspect.signature(last_observation_predictions).parameters) == (
        "observations", "mask"
    )
    assert tuple(inspect.signature(simple_heuristic_predictions).parameters) == (
        "observations", "mask"
    )


def test_last_observation_mask_and_fallback_handling():
    observations, mask = _small_inputs()
    prediction = last_observation_predictions(observations, mask)
    expected = np.asarray([0.2, 0.3, 0.4, 0.5, 0.6], dtype=np.float32)
    assert np.array_equal(prediction[0, 0, 0], np.zeros(5, dtype=np.float32))
    assert np.allclose(prediction[0, 1, 0], expected)
    assert np.allclose(prediction[0, 2, 0], expected)


def test_last_observation_is_deterministic():
    observations, mask = _small_inputs()
    assert np.array_equal(
        last_observation_predictions(observations, mask),
        last_observation_predictions(observations.copy(), mask.copy()),
    )


def test_simple_heuristic_is_deterministic_and_confidence_weighted():
    observations, mask = _small_inputs()
    first = simple_heuristic_predictions(observations, mask)
    second = simple_heuristic_predictions(observations.copy(), mask.copy())
    assert np.array_equal(first, second)
    expected_primitives = 0.8 * observations[0, 1, 0, :4] + 0.2 * 0.6
    expected_condition = 0.8 * 0.6 + 0.2 * observations[0, 1, 0, :4].mean()
    assert np.allclose(first[0, 1, 0, :4], expected_primitives)
    assert np.isclose(first[0, 1, 0, 4], expected_condition)
    assert np.allclose(first[0, 2, 0], first[0, 1, 0])


def test_metrics_have_required_shape_and_content():
    dataset = load_d0_release(D0)
    metrics = evaluate_baseline(
        dataset, "last_observation", "validation",
        generated_at_utc="2026-08-26T18:30:00Z",
    )
    assert metrics["number_of_scenarios"] == 2
    assert metrics["number_of_timestep_nodes"] == 80
    assert set(metrics["per_state_dimension_mae"]) == set(dataset.manifest["state_fields"])
    assert metrics["observed_node_error"]["count"] > 0
    assert metrics["unobserved_node_error"]["count"] > 0
    assert 0 <= metrics["mae_overall"] <= 1
    assert metrics["hidden_state_input"] is False
    assert metrics["training_performed"] is False


def test_output_json_schema_and_claim_boundary(tmp_path):
    comparison = run_d0_smoke_evaluation(
        D0, tmp_path, generated_at_utc="2026-08-26T18:30:00Z"
    )
    assert comparison["baseline_names"] == ["last_observation", "simple_heuristic"]
    assert comparison["debug_only"] is True
    assert comparison["training_performed"] is False
    assert "No Model 2 superiority claim" in comparison["claim_boundary"]
    for name in ("last_observation", "simple_heuristic"):
        payload = json.loads((tmp_path / f"{name}_metrics.json").read_text(encoding="utf-8"))
        assert set(payload) >= {"validation", "test", "input_files", "limitations"}
        assert payload["target_file_evaluation_only"] == "states.npy"
    saved = json.loads((tmp_path / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert saved == comparison


def test_smoke_run_creates_no_training_artifacts(tmp_path):
    run_d0_smoke_evaluation(D0, tmp_path, generated_at_utc="2026-08-26T18:30:00Z")
    assert {path.name for path in tmp_path.iterdir()} == {
        "last_observation_metrics.json",
        "simple_heuristic_metrics.json",
        "baseline_comparison.json",
    }
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.onnx"))
    assert not list(tmp_path.rglob("*.ckpt"))
