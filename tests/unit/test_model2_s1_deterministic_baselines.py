from __future__ import annotations

import json
from pathlib import Path

from oceansense.model2.s1_deterministic import (
    S1_COMPARISON_NAME,
    S1_OUTPUT_NAMES,
    evaluate_s1_deterministic_baseline,
    load_s1_deterministic_release,
    run_s1_deterministic_evaluation,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/model2/s1_learned_baseline_eval.json"
S1 = ROOT / "data/model2/s1_synthetic"


def test_s1_loader_binds_frozen_release_and_expected_shapes() -> None:
    dataset = load_s1_deterministic_release(CONFIG, ROOT)

    assert dataset.release_dir == S1
    assert dataset.manifest["release_id"] == "twin2-s1-synthetic-v1"
    assert dataset.states.shape == (200, 5, 10, 5)
    assert dataset.observations.shape == (200, 5, 10, 6)
    assert dataset.observation_mask.shape == (200, 5, 10)


def test_s1_metrics_cover_validation_test_and_ood() -> None:
    dataset = load_s1_deterministic_release(CONFIG, ROOT)
    expected_counts = {"validation": 32, "test": 24, "ood": 24}

    for split, count in expected_counts.items():
        metrics = evaluate_s1_deterministic_baseline(
            dataset,
            "last_observation",
            split,
            generated_at_utc="2026-08-30T00:00:00Z",
        )
        assert metrics["number_of_scenarios"] == count
        assert metrics["training_performed"] is False
        assert metrics["hidden_state_input"] is False
        assert metrics["synthetic_only"] is True
        assert set(metrics["per_state_dimension_mae"]) == set(
            dataset.manifest["state_fields"]
        )


def test_s1_run_writes_only_three_no_training_artifacts(tmp_path: Path) -> None:
    comparison = run_s1_deterministic_evaluation(
        CONFIG,
        ROOT,
        tmp_path,
        generated_at_utc="2026-08-30T00:00:00Z",
    )

    assert {path.name for path in tmp_path.iterdir()} == {
        *S1_OUTPUT_NAMES.values(),
        S1_COMPARISON_NAME,
    }
    assert comparison["baseline_names"] == ["last_observation", "simple_heuristic"]
    assert comparison["training_performed"] is False
    assert comparison["model1_status"] == "BLOCKED_NOT_FROZEN"
    assert "superiority" in comparison["claim_boundary"]
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.ckpt"))
    assert not list(tmp_path.rglob("*.onnx"))

    for filename in S1_OUTPUT_NAMES.values():
        payload = json.loads((tmp_path / filename).read_text(encoding="utf-8"))
        assert set(payload) >= {"validation", "test", "ood", "limitations"}
        assert payload["target_file_evaluation_only"] == "states.npy"


def test_s1_deterministic_run_is_reproducible_with_fixed_timestamp(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    timestamp = "2026-08-30T00:00:00Z"

    run_s1_deterministic_evaluation(CONFIG, ROOT, first, generated_at_utc=timestamp)
    run_s1_deterministic_evaluation(CONFIG, ROOT, second, generated_at_utc=timestamp)

    for filename in (*S1_OUTPUT_NAMES.values(), S1_COMPARISON_NAME):
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
