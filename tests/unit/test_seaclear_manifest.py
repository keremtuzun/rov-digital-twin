import csv
import json
from pathlib import Path

import pytest

from oceansense.seaclear import build_source_manifest


def _fixture(root: Path, *, duplicate: bool = False) -> None:
    first = root / "Site A" / "Camera One" / "1.jpg"
    second = root / "Site B" / "Camera Two" / "2.jpg"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_bytes(b"first-image")
    second.write_bytes(b"second-image")
    if duplicate:
        copy = root / "Site C" / "Camera Three" / "1.jpg"
        copy.parent.mkdir(parents=True)
        copy.write_bytes(b"duplicate-basename")
    payload = {
        "images": [
            {"id": 1, "file_name": "1.jpg", "width": 10, "height": 20},
            {"id": 2, "file_name": "2.jpg", "width": 30, "height": 40},
        ],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1},
            {"id": 2, "image_id": 2, "category_id": 2},
        ],
        "categories": [
            {"id": 1, "name": "bottle_plastic"},
            {"id": 2, "name": "animal_fish"},
        ],
    }
    (root / "dataset.json").write_text(json.dumps(payload), encoding="utf-8")


def test_build_source_manifest_hashes_assets_and_keeps_groups(tmp_path):
    root = tmp_path / "source"
    _fixture(root)
    output = tmp_path / "manifest.csv"
    summary_path = tmp_path / "summary.json"

    summary = build_source_manifest(root, output, summary_path)

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert summary["rows"] == 2
    assert summary["all_assets_hashed"] is True
    assert rows[0]["source_group"] == "Site A/Camera One"
    assert rows[0]["proposed_condition"] == "marine_debris"
    assert rows[1]["proposed_condition"] == "fish_or_habitat_activity"
    assert {row["approval_status"] for row in rows} == {"pending_review"}
    assert all(len(row["sha256"]) == 64 for row in rows)


def test_build_source_manifest_rejects_duplicate_basenames(tmp_path):
    root = tmp_path / "source"
    _fixture(root, duplicate=True)
    with pytest.raises(ValueError, match="basenames are not unique"):
        build_source_manifest(root, tmp_path / "manifest.csv", tmp_path / "summary.json")
