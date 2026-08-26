"""Fail-closed intake and comparison for completed SeaClear reviewer submissions."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oceansense.seaclear_review import TIMESTAMP_PATTERN
from oceansense.seaclear_reviewer_packages import (
    ALLOWED_DECISIONS,
    ALLOWED_REVIEWER_CONFIDENCE,
    PACKAGE_FIELDS,
    REVIEWER_FIELDS,
    sha256_file,
)

PROTECTED_FIELDS = tuple(field for field in PACKAGE_FIELDS if field not in REVIEWER_FIELDS)
COMPARISON_FIELDS = (
    "review_id", "image_id", "image_path_or_relative_key", "image_sha256",
    "source_category_names", "suggested_model1_label",
    "reviewer_1_decision", "reviewer_1_label", "reviewer_1_confidence",
    "reviewer_1_notes", "reviewer_1_timestamp",
    "reviewer_2_decision", "reviewer_2_label", "reviewer_2_confidence",
    "reviewer_2_notes", "reviewer_2_timestamp", "comparison_class",
)
ADJUDICATION_FIELDS = (
    "review_id", "image_id", "image_path_or_relative_key", "image_sha256",
    "source_category_names", "suggested_model1_label",
    "reviewer_1_decision", "reviewer_1_label", "reviewer_1_confidence",
    "reviewer_1_notes", "reviewer_2_decision", "reviewer_2_label",
    "reviewer_2_confidence", "reviewer_2_notes", "adjudicator_label",
    "adjudicator_decision", "adjudicator_notes", "adjudication_timestamp",
)
INVALID_FIELDS = ("review_id", "image_id", "reviewer", "error_code", "error_message")
AGREEMENT_CLASSES = ("agreement_approve", "agreement_reject", "agreement_unknown")
DISAGREEMENT_CLASSES = (
    "disagreement_label", "disagreement_decision", "needs_adjudication"
)


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _schema_labels(path: Path) -> tuple[str, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels = tuple(payload.get("allowed_model1_label_values", ()))
    if not labels:
        raise ValueError("review schema does not declare allowed_model1_label_values")
    return labels


def _add_error(
    errors: list[dict[str, str]], row: dict[str, str] | None, reviewer: str,
    code: str, message: str,
) -> None:
    errors.append({
        "review_id": (row or {}).get("review_id", ""),
        "image_id": (row or {}).get("image_id", ""),
        "reviewer": reviewer,
        "error_code": code,
        "error_message": message,
    })


def validate_submission(
    submission_path: str | Path,
    package_path: str | Path,
    allowed_labels: tuple[str, ...],
    *, reviewer: str,
) -> dict[str, Any]:
    """Validate a completed submission against its immutable blinded template."""
    submission = Path(submission_path)
    package = Path(package_path)
    fields, rows = _read_csv(submission)
    package_fields, package_rows = _read_csv(package)
    errors: list[dict[str, str]] = []
    if package_fields != PACKAGE_FIELDS:
        raise ValueError(f"invalid original package contract: {package}")
    if len(fields) != len(PACKAGE_FIELDS) or set(fields) != set(PACKAGE_FIELDS):
        _add_error(
            errors, None, reviewer, "invalid_columns",
            "submission columns must exactly match the blinded package contract",
        )
        return {"valid": False, "valid_rows": {}, "errors": errors, "row_count": len(rows)}

    expected = {row["review_id"]: row for row in package_rows}
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["review_id"].strip(), []).append(row)
    invalid_ids: set[str] = set()
    for review_id, duplicates in grouped.items():
        if not review_id:
            _add_error(errors, duplicates[0], reviewer, "missing_review_id", "review_id is blank")
            invalid_ids.add(review_id)
        elif len(duplicates) != 1:
            _add_error(
                errors, duplicates[0], reviewer, "duplicate_review_id",
                f"review_id occurs {len(duplicates)} times",
            )
            invalid_ids.add(review_id)
        elif review_id not in expected:
            _add_error(errors, duplicates[0], reviewer, "unexpected_review_id", "not in package")
            invalid_ids.add(review_id)
    for review_id, expected_row in expected.items():
        if review_id not in grouped:
            _add_error(errors, expected_row, reviewer, "missing_review_id", "row is absent")
            invalid_ids.add(review_id)

    valid_rows: dict[str, dict[str, str]] = {}
    for review_id in sorted(set(expected) & set(grouped)):
        if review_id in invalid_ids:
            continue
        row = grouped[review_id][0]
        row_errors: list[tuple[str, str]] = []
        for field in PROTECTED_FIELDS:
            if row[field] != expected[review_id][field]:
                row_errors.append((f"mismatched_{field}", f"{field} differs from package"))
        decision = row["reviewer_decision"].strip()
        label = row["reviewer_label"].strip()
        confidence = row["reviewer_confidence"].strip()
        notes = row["reviewer_notes"].strip()
        timestamp = row["review_timestamp"].strip()
        if decision not in ALLOWED_DECISIONS:
            row_errors.append(("invalid_decision", "reviewer_decision is missing or invalid"))
        if confidence not in ALLOWED_REVIEWER_CONFIDENCE:
            row_errors.append(("invalid_confidence", "reviewer_confidence is missing or invalid"))
        if not timestamp or not TIMESTAMP_PATTERN.fullmatch(timestamp):
            row_errors.append(("invalid_timestamp", "valid UTC review_timestamp is required"))
        if decision == "approve_suggestion":
            if label not in allowed_labels or label != row["suggested_model1_label"]:
                row_errors.append(("invalid_label", "approved label must equal the suggestion"))
        elif decision == "change_label":
            if label not in allowed_labels or label == row["suggested_model1_label"]:
                row_errors.append(("invalid_label", "changed label must be allowed and differ"))
        elif decision == "reject_image" and label:
            row_errors.append(("invalid_label", "rejected image must have a blank reviewer_label"))
        elif decision == "mark_unknown" and label != "unknown":
            row_errors.append(("invalid_label", "mark_unknown requires reviewer_label=unknown"))
        elif decision == "needs_adjudication" and label not in allowed_labels:
            row_errors.append(("invalid_label", "adjudication request requires an allowed label"))
        if (decision in {"reject_image", "mark_unknown", "needs_adjudication"} or confidence == "low") and not notes:
            row_errors.append(("missing_notes", "decision/confidence requires reviewer_notes"))
        if row_errors:
            for code, message in row_errors:
                _add_error(errors, row, reviewer, code, message)
        else:
            valid_rows[review_id] = row
    return {
        "valid": not errors,
        "valid_rows": valid_rows,
        "errors": errors,
        "row_count": len(rows),
    }


def _classification(row_1: dict[str, str], row_2: dict[str, str]) -> str:
    decision_1, decision_2 = row_1["reviewer_decision"], row_2["reviewer_decision"]
    if "needs_adjudication" in {decision_1, decision_2}:
        return "needs_adjudication"
    if decision_1 != decision_2:
        return "disagreement_decision"
    if decision_1 == "reject_image":
        return "agreement_reject"
    if decision_1 == "mark_unknown":
        return "agreement_unknown"
    if row_1["reviewer_label"] != row_2["reviewer_label"]:
        return "disagreement_label"
    return "agreement_approve"


def _comparison_row(
    source: dict[str, str], row_1: dict[str, str], row_2: dict[str, str], category: str
) -> dict[str, str]:
    result = {field: source.get(field, "") for field in COMPARISON_FIELDS}
    for number, row in ((1, row_1), (2, row_2)):
        for target, source_field in (
            ("decision", "reviewer_decision"), ("label", "reviewer_label"),
            ("confidence", "reviewer_confidence"), ("notes", "reviewer_notes"),
            ("timestamp", "review_timestamp"),
        ):
            result[f"reviewer_{number}_{target}"] = row[source_field]
    result["comparison_class"] = category
    return result


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            check=True, timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def compare_submissions(
    reviewer_1_path: str | Path,
    reviewer_2_path: str | Path,
    package_dir: str | Path,
    schema_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Validate, compare, and write non-approval review artifacts."""
    paths = [Path(reviewer_1_path), Path(reviewer_2_path), Path(schema_path)]
    package_path = Path(package_dir)
    paths.extend((package_path / "reviewer_1_queue.csv", package_path / "reviewer_2_queue.csv"))
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"required input files missing: {missing}")
    allowed_labels = _schema_labels(Path(schema_path))
    validation_1 = validate_submission(
        reviewer_1_path, package_path / "reviewer_1_queue.csv", allowed_labels,
        reviewer="reviewer_1",
    )
    validation_2 = validate_submission(
        reviewer_2_path, package_path / "reviewer_2_queue.csv", allowed_labels,
        reviewer="reviewer_2",
    )
    _, package_rows = _read_csv(package_path / "reviewer_1_queue.csv")
    source_by_id = {row["review_id"]: row for row in package_rows}
    invalid_errors = [*validation_1["errors"], *validation_2["errors"]]
    invalid_ids = {error["review_id"] for error in invalid_errors if error["review_id"]}
    if any(not error["review_id"] for error in invalid_errors):
        invalid_ids.update(source_by_id)

    comparison_rows: list[dict[str, str]] = []
    classes: Counter[str] = Counter()
    common_valid_ids = set(validation_1["valid_rows"]) & set(validation_2["valid_rows"])
    for review_id in sorted(common_valid_ids - invalid_ids):
        row_1 = validation_1["valid_rows"][review_id]
        row_2 = validation_2["valid_rows"][review_id]
        category = _classification(row_1, row_2)
        classes[category] += 1
        comparison_rows.append(_comparison_row(source_by_id[review_id], row_1, row_2, category))
    agreements = [row for row in comparison_rows if row["comparison_class"] in AGREEMENT_CLASSES]
    disagreements = [
        row for row in comparison_rows if row["comparison_class"] in DISAGREEMENT_CLASSES
    ]
    adjudication_rows = []
    for row in disagreements:
        target = {field: row.get(field, "") for field in ADJUDICATION_FIELDS}
        for field in (
            "adjudicator_label", "adjudicator_decision", "adjudicator_notes",
            "adjudication_timestamp",
        ):
            target[field] = ""
        adjudication_rows.append(target)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    _write_csv(output_path / "reviewer_agreements.csv", COMPARISON_FIELDS, agreements)
    _write_csv(output_path / "reviewer_disagreements.csv", COMPARISON_FIELDS, disagreements)
    _write_csv(output_path / "adjudication_queue.csv", ADJUDICATION_FIELDS, adjudication_rows)
    _write_csv(output_path / "reviewer_invalid_rows.csv", INVALID_FIELDS, invalid_errors)
    labels_1 = Counter(row["reviewer_label"] for row in validation_1["valid_rows"].values() if row["reviewer_label"])
    labels_2 = Counter(row["reviewer_label"] for row in validation_2["valid_rows"].values() if row["reviewer_label"])
    agreed_labels = Counter(
        row["reviewer_1_label"] for row in agreements if row["reviewer_1_label"]
    )
    valid_count = len(comparison_rows)
    agreement_count = len(agreements)
    summary = {
        "status": "VALID" if not invalid_errors else "VALIDATION_FAILED",
        "model1_status": "BLOCKED_NOT_FROZEN",
        "input_files": {
            "reviewer_1": str(Path(reviewer_1_path)),
            "reviewer_2": str(Path(reviewer_2_path)),
        },
        "input_sha256": {
            "reviewer_1": sha256_file(reviewer_1_path),
            "reviewer_2": sha256_file(reviewer_2_path),
        },
        "total_rows": len(source_by_id),
        "valid_rows": valid_count,
        "invalid_rows": len(invalid_ids),
        "invalid_error_count": len(invalid_errors),
        "agreement_counts": {key: classes[key] for key in AGREEMENT_CLASSES},
        "disagreement_counts": {key: classes[key] for key in DISAGREEMENT_CLASSES},
        "adjudication_queue_count": len(adjudication_rows),
        "rejection_count": sum(
            row["reviewer_1_decision"] == "reject_image" or row["reviewer_2_decision"] == "reject_image"
            for row in comparison_rows
        ),
        "unknown_count": sum(
            row["reviewer_1_decision"] == "mark_unknown" or row["reviewer_2_decision"] == "mark_unknown"
            for row in comparison_rows
        ),
        "per_label_counts": {
            "reviewer_1": dict(sorted(labels_1.items())),
            "reviewer_2": dict(sorted(labels_2.items())),
            "agreements": dict(sorted(agreed_labels.items())),
        },
        "reviewer_agreement_rate": agreement_count / valid_count if valid_count else 0.0,
        "approved_labels_created": 0,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "git_commit": _git_commit(),
    }
    (output_path / "reviewer_comparison_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
