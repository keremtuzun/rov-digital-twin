import csv
import json

from oceansense.seaclear_review import REVIEW_FIELDS, build_review_queue, validate_review_queue


def _write_fixture(tmp_path):
    staging = tmp_path / "staging.csv"
    fields = [
        "source_image_id", "relative_path", "sha256", "site", "source_group",
        "category_names", "proposed_domain", "proposed_condition",
    ]
    with staging.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "source_image_id": "7", "relative_path": "Site/Camera/7.jpg", "sha256": "a" * 64,
            "site": "Site", "source_group": "Site/Camera", "category_names": "bottle_plastic",
            "proposed_domain": "contamination", "proposed_condition": "marine_debris",
        })
    coco = tmp_path / "dataset.json"
    coco.write_text(json.dumps({"annotations": [
        {"id": 10, "image_id": 7, "category_id": 1},
        {"id": 11, "image_id": 7, "category_id": 1},
    ]}), encoding="utf-8")
    return staging, coco


def test_build_review_queue_is_all_pending_and_unapproved(tmp_path):
    staging, coco = _write_fixture(tmp_path)
    queue = tmp_path / "queue.csv"
    schema = tmp_path / "schema.json"
    report = build_review_queue(staging, coco, queue, schema)
    with queue.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert report["valid"] is True
    assert report["rows"] == 1
    assert set(rows[0]) == set(REVIEW_FIELDS)
    assert rows[0]["source_annotation_ids"] == "10;11"
    assert rows[0]["review_status"] == "pending_review"
    assert rows[0]["reviewer_1_label"] == ""
    assert rows[0]["approved_for_training"] == "false"
    assert json.loads(schema.read_text())["allowed_status_values"] == [
        "pending_review", "needs_adjudication", "approved", "rejected",
    ]


def test_validator_rejects_fake_pending_approval(tmp_path):
    staging, coco = _write_fixture(tmp_path)
    queue = tmp_path / "queue.csv"
    build_review_queue(staging, coco, queue, tmp_path / "schema.json")
    with queue.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["approved_for_training"] = "true"
    with queue.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report = validate_review_queue(queue)
    assert report["valid"] is False
    assert any("pending row carries approval" in error for error in report["errors"])
