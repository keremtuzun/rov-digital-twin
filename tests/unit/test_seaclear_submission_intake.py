import csv
import json

import pytest

from oceansense.seaclear_reviewer_packages import PACKAGE_FIELDS
from oceansense.seaclear_submission_intake import compare_submissions, validate_submission
from scripts.compare_seaclear_reviewer_submissions import main

LABELS = ("marine_debris", "poor_visibility", "biofouling", "unknown")


def _write_csv(path, rows, fields=PACKAGE_FIELDS):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _base_rows():
    rows = []
    for index in range(2):
        rows.append({
            "review_id": f"review-{index}",
            "image_id": str(index),
            "image_path_or_relative_key": f"site/camera/{index}.jpg",
            "image_sha256": f"{index + 1:064x}",
            "source_dataset": "SeaClear v1",
            "source_site": "site",
            "source_camera_or_group": "site/camera",
            "source_category_names": "bottle_plastic",
            "suggested_model1_label": "marine_debris",
            "suggestion_confidence": "medium",
            "reviewer_label": "",
            "reviewer_confidence": "",
            "reviewer_notes": "",
            "reviewer_decision": "",
            "review_timestamp": "",
        })
    return rows


def _completed(rows):
    completed = [dict(row) for row in rows]
    for row in completed:
        row.update({
            "reviewer_label": "marine_debris",
            "reviewer_confidence": "high",
            "reviewer_notes": "visible plastic object",
            "reviewer_decision": "approve_suggestion",
            "review_timestamp": "2026-08-26T18:00:00Z",
        })
    return completed


def _fixture(tmp_path):
    package_dir = tmp_path / "packages"
    base = _base_rows()
    _write_csv(package_dir / "reviewer_1_queue.csv", base)
    _write_csv(package_dir / "reviewer_2_queue.csv", list(reversed(base)))
    reviewer_1 = tmp_path / "reviewer_1.csv"
    reviewer_2 = tmp_path / "reviewer_2.csv"
    _write_csv(reviewer_1, _completed(base))
    _write_csv(reviewer_2, _completed(list(reversed(base))))
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"allowed_model1_label_values": LABELS}), encoding="utf-8")
    return reviewer_1, reviewer_2, package_dir, schema


def _read(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_matching_completed_submissions_produce_agreements_only(tmp_path):
    reviewer_1, reviewer_2, package_dir, schema = _fixture(tmp_path)
    output = tmp_path / "results"
    summary = compare_submissions(reviewer_1, reviewer_2, package_dir, schema, output)
    assert summary["status"] == "VALID"
    assert summary["valid_rows"] == 2
    assert summary["agreement_counts"]["agreement_approve"] == 2
    assert len(_read(output / "reviewer_agreements.csv")) == 2
    assert _read(output / "reviewer_disagreements.csv") == []
    assert _read(output / "adjudication_queue.csv") == []
    assert not (tmp_path / "labels.csv").exists()


def test_mismatched_image_hash_fails(tmp_path):
    reviewer_1, reviewer_2, package_dir, schema = _fixture(tmp_path)
    rows = _read(reviewer_1)
    rows[0]["image_sha256"] = "f" * 64
    _write_csv(reviewer_1, rows)
    summary = compare_submissions(
        reviewer_1, reviewer_2, package_dir, schema, tmp_path / "results"
    )
    assert summary["status"] == "VALIDATION_FAILED"
    assert summary["invalid_rows"] == 1
    assert any(
        row["error_code"] == "mismatched_image_sha256"
        for row in _read(tmp_path / "results" / "reviewer_invalid_rows.csv")
    )


def test_forbidden_approval_column_fails_closed(tmp_path):
    reviewer_1, _, package_dir, schema = _fixture(tmp_path)
    rows = _read(reviewer_1)
    fields = (*PACKAGE_FIELDS, "approved_for_training")
    for row in rows:
        row["approved_for_training"] = "true"
    _write_csv(reviewer_1, rows, fields)
    report = validate_submission(
        reviewer_1, package_dir / "reviewer_1_queue.csv", LABELS, reviewer="reviewer_1"
    )
    assert report["valid"] is False
    assert report["errors"][0]["error_code"] == "invalid_columns"
    assert report["valid_rows"] == {}


@pytest.mark.parametrize(
    ("decision", "label", "confidence"),
    [
        ("reject_image", "", "high"),
        ("mark_unknown", "unknown", "medium"),
        ("needs_adjudication", "unknown", "medium"),
        ("approve_suggestion", "marine_debris", "low"),
    ],
)
def test_required_notes_are_enforced(tmp_path, decision, label, confidence):
    reviewer_1, _, package_dir, _ = _fixture(tmp_path)
    rows = _read(reviewer_1)
    rows[0].update({
        "reviewer_decision": decision,
        "reviewer_label": label,
        "reviewer_confidence": confidence,
        "reviewer_notes": "",
    })
    _write_csv(reviewer_1, rows)
    report = validate_submission(
        reviewer_1, package_dir / "reviewer_1_queue.csv", LABELS, reviewer="reviewer_1"
    )
    assert any(error["error_code"] == "missing_notes" for error in report["errors"])


def test_label_disagreement_produces_blank_adjudication_row(tmp_path):
    reviewer_1, reviewer_2, package_dir, schema = _fixture(tmp_path)
    rows_1, rows_2 = _read(reviewer_1), _read(reviewer_2)
    for rows, label in ((rows_1, "poor_visibility"), (rows_2, "biofouling")):
        target = next(row for row in rows if row["review_id"] == "review-0")
        target.update({
            "reviewer_decision": "change_label",
            "reviewer_label": label,
            "reviewer_notes": "visible evidence supports alternate class",
        })
    _write_csv(reviewer_1, rows_1)
    _write_csv(reviewer_2, rows_2)
    output = tmp_path / "results"
    summary = compare_submissions(reviewer_1, reviewer_2, package_dir, schema, output)
    assert summary["disagreement_counts"]["disagreement_label"] == 1
    adjudication = _read(output / "adjudication_queue.csv")
    assert len(adjudication) == 1
    assert adjudication[0]["review_id"] == "review-0"
    assert all(
        not adjudication[0][field]
        for field in (
            "adjudicator_label", "adjudicator_decision", "adjudicator_notes",
            "adjudication_timestamp",
        )
    )
    assert not (tmp_path / "labels.csv").exists()


def test_strict_cli_returns_nonzero_for_invalid_submission(tmp_path):
    reviewer_1, reviewer_2, package_dir, schema = _fixture(tmp_path)
    rows = _read(reviewer_1)
    rows[0]["image_id"] = "wrong"
    _write_csv(reviewer_1, rows)
    exit_code = main([
        "--reviewer-1", str(reviewer_1), "--reviewer-2", str(reviewer_2),
        "--package-dir", str(package_dir), "--schema", str(schema),
        "--output-dir", str(tmp_path / "results"), "--strict",
    ])
    assert exit_code == 2
    assert not (tmp_path / "labels.csv").exists()
