import hashlib
import json
import shutil
from pathlib import Path

import pytest

from oceansense.model2.release_validator import validate_release
from oceansense.model2.s1_release import build_s1_release

ROOT = Path(__file__).resolve().parents[2]
S1 = ROOT / "data/model2/s1_synthetic"
CONFIG = ROOT / "configs/model2/s1_synthetic_release.json"


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _refresh_checksum(release, filename):
    path = release / "checksums.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["files"][filename] = hashlib.sha256((release / filename).read_bytes()).hexdigest()
    _write_json(path, payload)


@pytest.fixture
def release_copy(tmp_path):
    output = tmp_path / "s1"
    shutil.copytree(S1, output)
    return output


def _codes(report):
    return {error["code"] for error in report["errors"]}


def test_s1_validates_and_required_splits_are_nonzero():
    report = validate_release(S1, require_synthetic_s1=True)
    assert report["valid"] is True
    assert report["summary"]["scenario_count"] == 200
    assert report["summary"]["split_counts"] == {
        "train": 120, "validation": 32, "test": 24, "ood": 24,
    }


def test_s1_generation_is_byte_reproducible(tmp_path):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    regenerated = tmp_path / "regenerated"
    report = build_s1_release(config, regenerated)
    assert report["valid"] is True
    original = json.loads((S1 / "checksums.json").read_text(encoding="utf-8"))
    repeated = json.loads((regenerated / "checksums.json").read_text(encoding="utf-8"))
    # Runtime provenance must truthfully differ across OS/Python versions. All
    # actual data, graph, split, config and manifest bytes must remain identical.
    assert original["algorithm"] == repeated["algorithm"]
    assert {k: v for k, v in original["files"].items() if k != "metadata.json"} == {
        k: v for k, v in repeated["files"].items() if k != "metadata.json"
    }
    original_metadata = json.loads((S1 / "metadata.json").read_text(encoding="utf-8"))
    repeated_metadata = json.loads((regenerated / "metadata.json").read_text(encoding="utf-8"))
    for field in ("runtime_notes", "dependencies"):
        original_metadata.pop(field)
        repeated_metadata.pop(field)
    assert original_metadata == repeated_metadata
    same_runtime = tmp_path / "same_runtime"
    assert build_s1_release(config, same_runtime)["valid"] is True
    assert (same_runtime / "checksums.json").read_bytes() == (
        regenerated / "checksums.json"
    ).read_bytes()


def test_ood_split_and_distribution_shift_exist():
    splits = json.loads((S1 / "splits.json").read_text(encoding="utf-8"))
    metadata = json.loads((S1 / "metadata.json").read_text(encoding="utf-8"))
    assert splits["splits"]["ood"]
    assert "unseen graph family" in splits["ood_definition"]["reasons"]
    ood_records = [row for row in metadata["scenario_records"] if row["split"] == "ood"]
    train_records = [row for row in metadata["scenario_records"] if row["split"] == "train"]
    assert {row["distribution"]["graph_family"] for row in ood_records} == {
        "mixed_structure"
    }
    assert "mixed_structure" not in {
        row["distribution"]["graph_family"] for row in train_records
    }


def test_lineage_leakage_fails_validation(release_copy):
    path = release_copy / "metadata.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    train_lineage = next(
        row["lineage_id"] for row in payload["scenario_records"] if row["split"] == "train"
    )
    validation_row = next(
        row for row in payload["scenario_records"] if row["split"] == "validation"
    )
    validation_row["lineage_id"] = train_lineage
    _write_json(path, payload)
    _refresh_checksum(release_copy, "metadata.json")
    assert "lineage_overlap" in _codes(
        validate_release(release_copy, require_synthetic_s1=True)
    )


def test_split_overlap_fails_validation(release_copy):
    path = release_copy / "splits.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["splits"]["validation"].append(payload["splits"]["train"][0])
    _write_json(path, payload)
    _refresh_checksum(release_copy, "splits.json")
    assert "split_overlap" in _codes(
        validate_release(release_copy, require_synthetic_s1=True)
    )


def test_checksum_mismatch_fails_validation(release_copy):
    with (release_copy / "metadata.json").open("a", encoding="utf-8") as handle:
        handle.write(" ")
    assert "checksum_mismatch" in _codes(
        validate_release(release_copy, require_synthetic_s1=True)
    )


def test_missing_ood_metadata_fails_validation(release_copy):
    path = release_copy / "splits.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("ood_definition")
    _write_json(path, payload)
    _refresh_checksum(release_copy, "splits.json")
    assert "missing_ood_metadata" in _codes(
        validate_release(release_copy, require_synthetic_s1=True)
    )


def test_hidden_state_leakage_fails_validation(release_copy):
    path = release_copy / "manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["inference_inputs"].append("states.npy")
    _write_json(path, payload)
    _refresh_checksum(release_copy, "manifest.json")
    assert "hidden_state_leakage" in _codes(
        validate_release(release_copy, require_synthetic_s1=True)
    )
