import json
import copy
import runpy
import shutil
from pathlib import Path

import numpy as np
import pytest
import torch

from oceansense.local_restart import (
    classification_metrics, conformal_quantile, forward_model, make_model,
    search_summary, structural_scenario, visual_scene,
    run,
)

PROTOCOL = json.loads((Path(__file__).resolve().parents[2] / "configs/restart_local_v1.json").read_text())


def test_visual_scene_is_reproducible_and_has_independent_labels():
    first, labels = visual_scene(17, 0, PROTOCOL["model1"])
    second, again = visual_scene(17, 0, PROTOCOL["model1"])
    assert first.shape == (4, 3, 64, 64)
    np.testing.assert_array_equal(first, second)
    np.testing.assert_array_equal(labels, again)
    assert len(set(labels.tolist())) == 4
    shifted, _ = visual_scene(17, 0, PROTOCOL["model1"], True)
    assert not np.array_equal(first, shifted)


def test_structural_scenario_preserves_mask_and_is_reproducible():
    first = structural_scenario(18, PROTOCOL["model2"])
    second = structural_scenario(18, PROTOCOL["model2"])
    for a, b in zip(first, second):
        np.testing.assert_array_equal(a, b)
    obs, mask, graph, truth = first
    assert obs.shape == (12, 10, 6) and truth.shape == (12, 10, 5)
    assert set(np.unique(mask)) <= {0, 1}
    assert np.isfinite(obs).all() and np.isfinite(truth).all()
    np.testing.assert_array_equal(graph, graph.T)


def test_finite_sample_conformal_quantile_and_invalid_inputs():
    assert conformal_quantile(np.arange(19)) == 17
    for values in ([], [1], [np.nan], [np.inf], [[1, 2]]):
        with pytest.raises(ValueError):
            conformal_quantile(values)


def test_search_does_not_claim_plateau_when_still_improving():
    candidates = [{"name": str(i)} for i in range(6)]
    rising = [{"candidate": str(i), "validation_score": i / 10} for i in range(6)]
    result = search_summary(rising, candidates, 0.01)
    assert result["status"] == "budget_exhausted"
    assert not result["physical_data_is_only_remaining_improvement"]
    flat = [{"candidate": str(i), "validation_score": 0.5} for i in range(6)]
    assert search_summary(flat, candidates, 0.01)["status"] == "bounded_search_plateau"


def test_classification_reports_missing_class_recall():
    result = classification_metrics(np.array([[0.9, 0.1], [0.9, 0.1]]), np.array([0, 1]))
    assert result["accuracy"] == 0.5
    assert result["minimum_class_recall"] == 0


@pytest.mark.parametrize("candidate", PROTOCOL["model2"]["candidates"])
def test_restart_models_remain_causal(candidate):
    torch.manual_seed(7)
    model = make_model("model2", candidate, PROTOCOL).eval()
    x = [torch.rand(1, 4, 10, 7), torch.ones(1, 10, 10),
         torch.ones(1, 4, 10), torch.ones(1, 4, 10)]
    changed = [v.clone() for v in x]
    changed[0][:, 2:] = torch.rand_like(changed[0][:, 2:])
    with torch.no_grad():
        a = forward_model(model, "model2", x)
        b = forward_model(model, "model2", changed)
    torch.testing.assert_close(a[:, :2], b[:, :2])
    assert a.shape == (1, 4, 10, 5)


def test_end_to_end_restart_and_saved_evidence_audit(tmp_path):
    root = Path(__file__).resolve().parents[2]
    protocol = copy.deepcopy(PROTOCOL)
    protocol["experiment_id"] = "smoke"
    protocol["splits"] = {"train": 4, "validation": 4, "calibration": 10, "test": 4, "ood": 4}
    protocol["training_seeds"] = [7]
    for model_id in ("model1", "model2"):
        protocol[model_id]["maximum_epochs"] = 1
        protocol[model_id]["candidates"] = protocol[model_id]["candidates"][:1]
    (tmp_path / "configs").mkdir()
    path = tmp_path / "configs/restart_local_v1.json"
    path.write_text(json.dumps(protocol))
    source = tmp_path / "src/oceansense/local_restart.py"
    source.parent.mkdir(parents=True)
    shutil.copyfile(root / "src/oceansense/local_restart.py", source)
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        result = run(tmp_path, path)
    finally:
        torch.set_num_threads(threads)
    assert not result["deployment_authorized"]
    assert not result["full_model1_taxonomy_trained"]
    audit = runpy.run_path(str(root / "scripts/audit_local_restart.py"))["audit"]
    assert audit(tmp_path, "smoke")["runs_verified"] == 2
    with pytest.raises(FileExistsError, match="repeat held-out"):
        run(tmp_path, path)
    predictions = tmp_path / "reports/smoke/model1_test_predictions.npy"
    predictions.write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        audit(tmp_path, "smoke")
