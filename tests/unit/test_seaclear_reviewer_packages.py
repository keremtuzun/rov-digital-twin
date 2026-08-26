import csv

from oceansense.seaclear_review import REVIEW_FIELDS
from oceansense.seaclear_reviewer_packages import (
    PACKAGE_FIELDS,
    REVIEWER_FIELDS,
    build_reviewer_packages,
    validate_reviewer_packages,
)


def _write_source(path, count=3):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for index in range(count):
            row = {field: "" for field in REVIEW_FIELDS}
            row.update({
                "review_id": f"review-{index}",
                "image_id": str(index),
                "image_path_or_relative_key": f"site/camera/{index}.jpg",
                "image_sha256": f"{index + 1:064x}",
                "source_dataset": "SeaClear v1",
                "source_site": "site",
                "source_camera_or_group": "site/camera",
                "source_category_names": "bottle_plastic",
                "suggested_model1_domain": "contamination",
                "suggested_model1_label": "marine_debris",
                "suggestion_confidence": "medium",
                "review_status": "pending_review",
                "approved_for_training": "false",
                "approved_for_validation": "false",
                "approved_for_test": "false",
            })
            writer.writerow(row)


def test_builds_two_blinded_reproducible_packages(tmp_path):
    source = tmp_path / "source.csv"
    output = tmp_path / "packages"
    _write_source(source)
    report = build_reviewer_packages(source, output, reviewer_1_seed=1, reviewer_2_seed=4)
    assert report["valid"] is True
    assert report["row_counts"] == {"reviewer_1": 3, "reviewer_2": 3}
    package_rows = []
    for reviewer in (1, 2):
        with (output / f"reviewer_{reviewer}_queue.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        assert tuple(reader.fieldnames) == PACKAGE_FIELDS
        assert all(not row[field] for row in rows for field in REVIEWER_FIELDS)
        assert not any("adjudicat" in field or "approved" in field for field in reader.fieldnames)
        package_rows.append(rows)
    assert {row["review_id"] for row in package_rows[0]} == {
        row["review_id"] for row in package_rows[1]
    }
    assert [row["review_id"] for row in package_rows[0]] != [
        row["review_id"] for row in package_rows[1]
    ]


def test_validator_rejects_leaked_or_completed_template(tmp_path):
    source = tmp_path / "source.csv"
    output = tmp_path / "packages"
    _write_source(source)
    build_reviewer_packages(source, output, reviewer_1_seed=1, reviewer_2_seed=2)
    queue = output / "reviewer_1_queue.csv"
    with queue.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["reviewer_label"] = "marine_debris"
    with queue.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PACKAGE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report = validate_reviewer_packages(output, expected_rows=3)
    assert report["valid"] is False
    assert any("reviewer fields must be blank" in error for error in report["errors"])
    assert any("SHA-256" in error for error in report["errors"])


def test_builder_rejects_non_pending_or_approved_source(tmp_path):
    source = tmp_path / "source.csv"
    _write_source(source, count=1)
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["approved_for_training"] = "true"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    try:
        build_reviewer_packages(source, tmp_path / "packages")
    except ValueError as exc:
        assert "approval flag" in str(exc)
    else:
        raise AssertionError("approved source row was accepted")
