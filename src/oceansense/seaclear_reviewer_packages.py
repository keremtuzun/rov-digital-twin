"""Create and validate independent, blinded SeaClear reviewer queues."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oceansense.seaclear_review import CONDITION_LABELS, CONFIDENCE_VALUES, REVIEW_FIELDS

PACKAGE_FIELDS = (
    "review_id",
    "image_id",
    "image_path_or_relative_key",
    "image_sha256",
    "source_dataset",
    "source_site",
    "source_camera_or_group",
    "source_category_names",
    "suggested_model1_label",
    "suggestion_confidence",
    "reviewer_label",
    "reviewer_confidence",
    "reviewer_notes",
    "reviewer_decision",
    "review_timestamp",
)
REVIEWER_FIELDS = (
    "reviewer_label",
    "reviewer_confidence",
    "reviewer_notes",
    "reviewer_decision",
    "review_timestamp",
)
ALLOWED_DECISIONS = (
    "approve_suggestion",
    "change_label",
    "reject_image",
    "mark_unknown",
    "needs_adjudication",
)
ALLOWED_REVIEWER_CONFIDENCE = ("high", "medium", "low")
DEFAULT_SEEDS = {"reviewer_1": 1101, "reviewer_2": 1102}
QUEUE_NAMES = {
    "reviewer_1": "reviewer_1_queue.csv",
    "reviewer_2": "reviewer_2_queue.csv",
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_pristine_source(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = set(REVIEW_FIELDS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"source review queue is missing fields: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("source review queue is empty")
    approval_fields = ("approved_for_training", "approved_for_validation", "approved_for_test")
    human_fields = tuple(
        field
        for field in REVIEW_FIELDS
        if field.startswith(("reviewer_", "adjudicat"))
    )
    for row_number, row in enumerate(rows, start=2):
        if row["review_status"] != "pending_review":
            raise ValueError(f"row {row_number}: source must remain pending_review")
        if any(row[field] != "false" for field in approval_fields):
            raise ValueError(f"row {row_number}: source contains an approval flag")
        if any(row[field].strip() for field in human_fields):
            raise ValueError(f"row {row_number}: source contains review or adjudication data")
    return rows


def _package_row(source: dict[str, str]) -> dict[str, str]:
    row = {field: source.get(field, "") for field in PACKAGE_FIELDS}
    for field in REVIEWER_FIELDS:
        row[field] = ""
    return row


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PACKAGE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_reviewer_packages(
    source_queue: str | Path,
    output_dir: str | Path,
    *,
    reviewer_1_seed: int = DEFAULT_SEEDS["reviewer_1"],
    reviewer_2_seed: int = DEFAULT_SEEDS["reviewer_2"],
) -> dict[str, Any]:
    """Build two reproducibly shuffled queues from an untouched central queue."""
    if reviewer_1_seed == reviewer_2_seed:
        raise ValueError("reviewer seeds must differ")
    source_path = Path(source_queue)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    source_rows = _load_pristine_source(source_path)
    seeds = {"reviewer_1": reviewer_1_seed, "reviewer_2": reviewer_2_seed}
    files: dict[str, dict[str, Any]] = {}
    for reviewer, filename in QUEUE_NAMES.items():
        rows = [_package_row(row) for row in source_rows]
        random.Random(seeds[reviewer]).shuffle(rows)
        queue_path = output_path / filename
        _write_queue(queue_path, rows)
        queue_hash = sha256_file(queue_path)
        (output_path / f"{filename}.sha256").write_text(
            f"{queue_hash}  {filename}\n", encoding="ascii"
        )
        files[reviewer] = {
            "path": filename,
            "rows": len(rows),
            "sha256": queue_hash,
            "shuffle_seed": seeds[reviewer],
        }
    manifest = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_queue": source_path.as_posix(),
        "source_queue_sha256": sha256_file(source_path),
        "columns": list(PACKAGE_FIELDS),
        "allowed_reviewer_decisions": list(ALLOWED_DECISIONS),
        "allowed_reviewer_confidence": list(ALLOWED_REVIEWER_CONFIDENCE),
        "blinding": "Each queue contains only one generic set of blank reviewer fields.",
        "approved_labels_created": 0,
        "files": files,
    }
    (output_path / "package_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return validate_reviewer_packages(output_path, expected_rows=len(source_rows))


def _read_package(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def validate_reviewer_packages(
    output_dir: str | Path, *, expected_rows: int = 8610, require_blank: bool = True
) -> dict[str, Any]:
    """Fail closed unless both package templates are complete, blinded, and unmodified."""
    output_path = Path(output_dir)
    errors: list[str] = []
    manifest_path = output_path / "package_manifest.json"
    if not manifest_path.is_file():
        return {"valid": False, "errors": ["package_manifest.json is missing"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"valid": False, "errors": [f"invalid package manifest: {exc}"]}

    packages: dict[str, list[dict[str, str]]] = {}
    row_counts: dict[str, int] = {}
    for reviewer, filename in QUEUE_NAMES.items():
        queue_path = output_path / filename
        if not queue_path.is_file():
            errors.append(f"{filename} is missing")
            continue
        fields, rows = _read_package(queue_path)
        packages[reviewer] = rows
        row_counts[reviewer] = len(rows)
        if fields != PACKAGE_FIELDS:
            errors.append(f"{filename}: columns must exactly match the blinded package contract")
        if len(rows) != expected_rows:
            errors.append(f"{filename}: expected {expected_rows} rows, found {len(rows)}")
        review_ids = [row.get("review_id", "").strip() for row in rows]
        if any(not review_id for review_id in review_ids) or len(set(review_ids)) != len(rows):
            errors.append(f"{filename}: review IDs must be non-empty and unique")
        for index, row in enumerate(rows, start=2):
            if require_blank and any(row.get(field, "").strip() for field in REVIEWER_FIELDS):
                errors.append(f"{filename} row {index}: initial reviewer fields must be blank")
                break
            if row.get("suggested_model1_label", "") not in ("", *CONDITION_LABELS):
                errors.append(f"{filename} row {index}: invalid suggested label")
                break
            if row.get("suggestion_confidence", "") not in CONFIDENCE_VALUES:
                errors.append(f"{filename} row {index}: invalid suggestion confidence")
                break
            if not re.fullmatch(r"[0-9a-f]{64}", row.get("image_sha256", "")):
                errors.append(f"{filename} row {index}: invalid image SHA-256")
                break
        actual_hash = sha256_file(queue_path)
        file_manifest = manifest.get("files", {}).get(reviewer, {})
        if file_manifest.get("sha256") != actual_hash:
            errors.append(f"{filename}: SHA-256 does not match package manifest")
        checksum_path = output_path / f"{filename}.sha256"
        expected_sidecar = f"{actual_hash}  {filename}\n"
        if not checksum_path.is_file() or checksum_path.read_text(encoding="ascii") != expected_sidecar:
            errors.append(f"{filename}: checksum sidecar is missing or invalid")

    if len(packages) == 2:
        identity_fields = ("review_id", "image_id", "image_path_or_relative_key", "image_sha256")
        identities = {
            reviewer: {tuple(row.get(field, "") for field in identity_fields) for row in rows}
            for reviewer, rows in packages.items()
        }
        if identities["reviewer_1"] != identities["reviewer_2"]:
            errors.append("reviewer queues do not contain the same review IDs and images")
        order_1 = [row.get("review_id", "") for row in packages["reviewer_1"]]
        order_2 = [row.get("review_id", "") for row in packages["reviewer_2"]]
        if len(order_1) > 1 and order_1 == order_2:
            errors.append("reviewer queues unexpectedly have identical order")
    if manifest.get("approved_labels_created") != 0:
        errors.append("manifest must state that zero approved labels were created")
    if tuple(manifest.get("columns", ())) != PACKAGE_FIELDS:
        errors.append("manifest columns do not match the blinded package contract")
    if (output_path.parent / "labels.csv").exists():
        errors.append("labels.csv must not be created by reviewer packaging")
    return {
        "valid": not errors,
        "errors": errors,
        "row_counts": row_counts,
        "reviewer_fields_blank": require_blank and not any(
            "reviewer fields" in error for error in errors
        ),
        "approved_labels_created": 0,
    }
