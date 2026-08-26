import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from oceansense.model2.d0_release import build_d0_release
from oceansense.model2.release_validator import validate_release
from scripts.validate_model2_release import main


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _refresh_checksum(release, filename):
    checksums_path = release / "checksums.json"
    payload = json.loads(checksums_path.read_text(encoding="utf-8"))
    payload["files"][filename] = hashlib.sha256((release / filename).read_bytes()).hexdigest()
    _write_json(checksums_path, payload)


@pytest.fixture(scope="module")
def valid_release(tmp_path_factory):
    root = Path(__file__).resolve().parents[2]
    config = json.loads(
        (root / "configs/model2/d0_debug_release.json").read_text(encoding="utf-8")
    )
    output = tmp_path_factory.mktemp("model2-release") / "valid"
    report = build_d0_release(config, output)
    assert report["valid"] is True
    return output


@pytest.fixture
def release_copy(tmp_path, valid_release):
    output = tmp_path / "release"
    shutil.copytree(valid_release, output)
    return output


def _codes(report):
    return {error["code"] for error in report["errors"]}


def test_valid_release_passes(valid_release):
    report = validate_release(valid_release, require_debug_d0=True)
    assert report["valid"] is True
    assert report["summary"]["split_counts"] == {"train": 19, "validation": 2, "test": 4}
    assert report["summary"]["training_performed"] is False


def test_release_generation_is_byte_reproducible(valid_release, tmp_path):
    root = Path(__file__).resolve().parents[2]
    config = json.loads(
        (root / "configs/model2/d0_debug_release.json").read_text(encoding="utf-8")
    )
    second = tmp_path / "second"
    build_d0_release(config, second)
    first_checksums = json.loads(
        (valid_release / "checksums.json").read_text(encoding="utf-8")
    )
    second_checksums = json.loads((second / "checksums.json").read_text(encoding="utf-8"))
    assert first_checksums == second_checksums


def test_missing_required_file_fails(release_copy):
    (release_copy / "states.npy").unlink()
    report = validate_release(release_copy)
    assert report["valid"] is False
    assert "missing_file" in _codes(report)


def test_checksum_mismatch_fails(release_copy):
    with (release_copy / "metadata.json").open("a", encoding="utf-8") as handle:
        handle.write(" ")
    report = validate_release(release_copy)
    assert "checksum_mismatch" in _codes(report)


def test_split_overlap_fails(release_copy):
    path = release_copy / "splits.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["splits"]["validation"].append(payload["splits"]["train"][0])
    _write_json(path, payload)
    _refresh_checksum(release_copy, "splits.json")
    assert "split_overlap" in _codes(validate_release(release_copy))


def test_missing_split_fails(release_copy):
    path = release_copy / "splits.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["splits"]["validation"] = []
    _write_json(path, payload)
    _refresh_checksum(release_copy, "splits.json")
    assert "missing_split" in _codes(validate_release(release_copy))


def test_state_shape_mismatch_fails(release_copy):
    path = release_copy / "states.npy"
    states = np.load(path, allow_pickle=False)
    np.save(path, states[..., :-1])
    _refresh_checksum(release_copy, "states.npy")
    assert "states_shape_mismatch" in _codes(validate_release(release_copy))


def test_mask_shape_mismatch_fails(release_copy):
    path = release_copy / "observation_mask.npy"
    mask = np.load(path, allow_pickle=False)
    np.save(path, mask[:-1])
    _refresh_checksum(release_copy, "observation_mask.npy")
    assert "mask_shape_mismatch" in _codes(validate_release(release_copy))


def test_invalid_mask_values_fail(release_copy):
    path = release_copy / "observation_mask.npy"
    mask = np.load(path, allow_pickle=False)
    mask[0, 0, 0] = 2
    np.save(path, mask)
    _refresh_checksum(release_copy, "observation_mask.npy")
    assert "invalid_mask_values" in _codes(validate_release(release_copy))


def test_graph_node_mismatch_fails(release_copy):
    path = release_copy / "structure_graph.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["scenario_graphs"][0]["nodes"].pop()
    _write_json(path, payload)
    _refresh_checksum(release_copy, "structure_graph.json")
    assert "graph_node_mismatch" in _codes(validate_release(release_copy))


def test_hidden_state_leakage_into_inference_inputs_fails(release_copy):
    path = release_copy / "manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["inference_inputs"].append("states.npy")
    _write_json(path, payload)
    _refresh_checksum(release_copy, "manifest.json")
    assert "hidden_state_leakage" in _codes(validate_release(release_copy))


def test_strict_cli_returns_nonzero_for_invalid_release(release_copy, tmp_path):
    (release_copy / "observations.npy").unlink()
    report_path = tmp_path / "validation.json"
    exit_code = main([
        "--release-dir", str(release_copy), "--strict", "--require-debug-d0",
        "--json-out", str(report_path),
    ])
    assert exit_code == 2
    assert json.loads(report_path.read_text(encoding="utf-8"))["valid"] is False
