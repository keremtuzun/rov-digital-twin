from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from oceansense.model2.graph_baselines import GraphBaseline, load_adjacency, masked_mse
from oceansense.model2.graph_training import run_graph_baseline, run_graph_seed
from oceansense.model2.independent_mlp import load_s1_data
from oceansense.model2.temporal_gru import _load_completed_seed, seed_temporal_gru

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/model2/s1_learned_baseline_eval.json"


def model(temporal=False):
    seed_temporal_gru(2026201)
    config = json.loads(CONFIG.read_text())
    name = "temporal_gnn" if temporal else "static_gnn"
    return GraphBaseline(7, 5, config["baseline_architecture_bounds"][name], temporal).eval()


@pytest.mark.parametrize("temporal", [False, True])
def test_shapes_finite_bounded_and_checkpoint_roundtrip(temporal, tmp_path):
    net = model(temporal)
    x, a = torch.randn(2, 5, 4, 7), torch.ones(2, 4, 4)
    expected = net(x, a)
    assert expected.shape == (2, 5, 4, 5)
    assert torch.all((expected >= 0) & (expected <= 1))
    torch.save(net.state_dict(), tmp_path / "weights.pt")
    restored = model(temporal)
    restored.load_state_dict(torch.load(tmp_path / "weights.pt", weights_only=True))
    assert torch.equal(expected, restored(x, a))


@pytest.mark.parametrize("temporal", [False, True])
def test_permutation_equivariance_and_scenario_isolation(temporal):
    net = model(temporal)
    x, a = torch.randn(2, 5, 4, 7), torch.rand(2, 4, 4)
    permutation = [2, 0, 3, 1]
    expected = net(x, a)
    actual = net(x[:, :, permutation], a[:, permutation][:, :, permutation])
    assert torch.allclose(actual, expected[:, :, permutation], atol=1e-6)
    x[1] += 50
    assert torch.equal(net(x, a)[0], expected[0])


@pytest.mark.parametrize("temporal", [False, True])
def test_no_future_leakage_or_persistent_cross_call_state(temporal):
    net = model(temporal)
    x, a = torch.randn(1, 5, 4, 7), torch.ones(1, 4, 4)
    expected = net(x, a)
    changed = x.clone()
    changed[:, 3:] += 100
    assert torch.equal(expected[:, :3], net(changed, a)[:, :3])
    assert torch.equal(expected, net(x, a))
    if not temporal:
        changed = x.clone()
        changed[:, :3] += 100
        assert torch.equal(expected[:, 3:], net(changed, a)[:, 3:])


def test_topology_matters_and_isolated_nodes_are_finite():
    net = model()
    x = torch.randn(1, 3, 4, 7)
    isolated = net(x, torch.zeros(1, 4, 4))
    assert torch.isfinite(isolated).all()
    assert not torch.equal(isolated, net(x, torch.ones(1, 4, 4)))


def test_graph_alignment_uses_ids_and_tensor_indices(tmp_path):
    _, data = load_s1_data(CONFIG, ROOT)
    expected = load_adjacency(data)
    payload = json.loads((data.release_dir / "structure_graph.json").read_text())
    payload["scenario_graphs"].reverse()
    for graph in payload["scenario_graphs"]:
        graph["nodes"].reverse()
    (tmp_path / "structure_graph.json").write_text(json.dumps(payload))
    assert np.array_equal(expected, load_adjacency(replace(data, release_dir=tmp_path)))
    payload["scenario_graphs"][0]["nodes"][0]["tensor_index"] = 999
    (tmp_path / "structure_graph.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="tensor indices"):
        load_adjacency(replace(data, release_dir=tmp_path))


def test_empty_supervision_fails_instead_of_nan():
    with pytest.raises(ValueError, match="no observed"):
        masked_mse(torch.zeros(1, 2, 3, 5), torch.ones(1, 2, 3, 5), torch.zeros(1, 2, 3))


@pytest.mark.parametrize("temporal", [False, True])
def test_seed_training_artifacts_and_overwrite_refusal(tmp_path, temporal):
    config, data = load_s1_data(CONFIG, ROOT)
    # Fixture only: shortened training is never written into the frozen experiment root.
    config["training_bounds"]["max_epochs"] = 1
    baseline = "temporal_gnn" if temporal else "static_gnn"
    config_path = tmp_path / "test_config.json"
    config_path.write_text(json.dumps(config))
    result = run_graph_seed(
        config, config_path, data, load_adjacency(data), tmp_path, 2026201, baseline
    )
    output = tmp_path / config["artifacts"]["root"] / baseline / "seed_2026201"
    assert (output / "completed.json").is_file()
    assert result["selected_checkpoint"]["test_used_for_selection"] is False
    for filename in config["artifacts"]["required_per_seed"].values():
        assert (output / filename).is_file()
    with pytest.raises(FileExistsError):
        run_graph_seed(config, config_path, data, load_adjacency(data), tmp_path, 2026201, baseline)


def test_unknown_baseline_is_rejected_before_writing(tmp_path):
    with pytest.raises(ValueError, match="unknown"):
        run_graph_baseline(CONFIG, tmp_path, "proprietary_model2")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("corruption", ["config", "inventory", "filename"])
def test_gru_recovery_rejects_corrupted_metadata(tmp_path, corruption):
    import shutil

    config, data = load_s1_data(CONFIG, ROOT)
    relative = Path(config["artifacts"]["root"]) / "temporal_gru/seed_2026201"
    output = tmp_path / relative
    shutil.copytree(ROOT / relative, output)
    name = "config.json" if corruption == "config" else "prediction_summary.json"
    payload = json.loads((output / name).read_text())
    if corruption == "config":
        payload["training_seeds"] = [1, 2, 3]
    elif corruption == "inventory":
        payload["predictions"] = {}
    else:
        payload["predictions"]["test"]["file"] = "../outside.npy"
    (output / name).write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="mismatch|filename"):
        _load_completed_seed(config, data, tmp_path, 2026201)
