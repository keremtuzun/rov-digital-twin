"""Fail-closed SeaClear double-review queue generation and validation."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DOMAIN_LABELS = (
    "structure",
    "nature_ecology",
    "contamination",
    "fishing_aquaculture",
    "general_underwater",
    "unknown",
)
CONDITION_LABELS = (
    "normal_or_no_visible_concern",
    "possible_structural_concern",
    "biofouling",
    "marine_debris",
    "poor_visibility",
    "ecological_stress_indicator",
    "fish_or_habitat_activity",
    "aquaculture_infrastructure_concern",
    "unknown",
)
STATUS_VALUES = ("pending_review", "needs_adjudication", "approved", "rejected")
REJECTION_REASONS = (
    "corrupt_image",
    "unreadable_image",
    "duplicate_or_near_duplicate",
    "rights_or_provenance_issue",
    "no_relevant_visual_evidence",
    "ambiguous_source_annotation",
    "unsupported_model1_semantics",
    "severe_occlusion",
    "severe_blur",
    "severe_visibility_loss",
    "reviewer_conflict_unresolved",
    "other_documented",
)
CONFIDENCE_VALUES = ("none", "low", "medium", "high")
REVIEW_FIELDS = (
    "review_id",
    "image_id",
    "image_path_or_relative_key",
    "image_sha256",
    "source_dataset",
    "source_site",
    "source_camera_or_group",
    "source_annotation_ids",
    "source_category_names",
    "suggested_model1_domain",
    "suggested_model1_label",
    "suggestion_confidence",
    "review_status",
    "reviewer_1_id",
    "reviewer_1_domain",
    "reviewer_1_label",
    "reviewer_1_notes",
    "reviewer_1_timestamp",
    "reviewer_2_id",
    "reviewer_2_domain",
    "reviewer_2_label",
    "reviewer_2_notes",
    "reviewer_2_timestamp",
    "adjudicator_id",
    "adjudicated_domain",
    "adjudicated_label",
    "adjudicator_notes",
    "adjudication_timestamp",
    "approved_for_training",
    "approved_for_validation",
    "approved_for_test",
    "rejection_reason",
)
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def review_schema() -> dict[str, Any]:
    string = {"type": "string"}
    properties = {field: dict(string) for field in REVIEW_FIELDS}
    properties.update(
        {
            "image_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "suggested_model1_domain": {"type": "string", "enum": ["", *DOMAIN_LABELS]},
            "suggested_model1_label": {"type": "string", "enum": ["", *CONDITION_LABELS]},
            "suggestion_confidence": {"type": "string", "enum": list(CONFIDENCE_VALUES)},
            "review_status": {"type": "string", "enum": list(STATUS_VALUES)},
            "reviewer_1_domain": {"type": "string", "enum": ["", *DOMAIN_LABELS]},
            "reviewer_1_label": {"type": "string", "enum": ["", *CONDITION_LABELS]},
            "reviewer_2_domain": {"type": "string", "enum": ["", *DOMAIN_LABELS]},
            "reviewer_2_label": {"type": "string", "enum": ["", *CONDITION_LABELS]},
            "adjudicated_domain": {"type": "string", "enum": ["", *DOMAIN_LABELS]},
            "adjudicated_label": {"type": "string", "enum": ["", *CONDITION_LABELS]},
            "reviewer_1_timestamp": {"type": "string", "pattern": "^(|\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z)$"},
            "reviewer_2_timestamp": {"type": "string", "pattern": "^(|\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z)$"},
            "adjudication_timestamp": {"type": "string", "pattern": "^(|\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z)$"},
            "approved_for_training": {"type": "string", "enum": ["false", "true"]},
            "approved_for_validation": {"type": "string", "enum": ["false", "true"]},
            "approved_for_test": {"type": "string", "enum": ["false", "true"]},
            "rejection_reason": {"type": "string", "enum": ["", *REJECTION_REASONS]},
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "SeaClear Model 1 Human Label Review Row",
        "schema_version": "1.0.0",
        "type": "object",
        "required": list(REVIEW_FIELDS),
        "additionalProperties": False,
        "properties": properties,
        "allowed_status_values": list(STATUS_VALUES),
        "allowed_model1_domain_values": list(DOMAIN_LABELS),
        "allowed_model1_label_values": list(CONDITION_LABELS),
        "allowed_rejection_reasons": list(REJECTION_REASONS),
        "timestamp_format": "UTC RFC3339: YYYY-MM-DDTHH:MM:SS[.ffffff]Z",
        "reviewer_requirements": [
            "two distinct identifiable reviewers per image",
            "reviewers submit independently and cannot see the other's decision before submission",
            "unknown, rejected, or ambiguous decisions require notes",
        ],
        "adjudication_requirements": [
            "reviewer disagreement requires needs_adjudication",
            "adjudicator must be identifiable and different from both reviewers",
            "adjudicated domain, label, notes, and timestamp are required for an approved disagreement",
        ],
        "validation_rules": [
            "pending rows cannot carry approval flags or adjudicated values",
            "needs_adjudication requires two complete independent reviews and no approval flags",
            "rejected rows require a rejection reason and cannot carry approval flags",
            "approved rows require two complete reviews and at least one explicit use-approval flag",
            "disagreed approved rows require a complete independent adjudication",
            "source suggestions are non-binding and never count as human approval",
        ],
    }


def _confidence(label: str) -> str:
    return {
        "marine_debris": "medium",
        "fish_or_habitat_activity": "low",
        "unknown": "low",
        "": "none",
    }[label]


def build_review_queue(
    staging_manifest: str | Path,
    coco_json: str | Path,
    output_csv: str | Path,
    schema_json: str | Path,
) -> dict[str, Any]:
    """Create a new all-pending queue; callers must prevent accidental overwrite."""
    with Path(staging_manifest).open(newline="", encoding="utf-8-sig") as handle:
        staging_rows = list(csv.DictReader(handle))
    payload = json.loads(Path(coco_json).read_text(encoding="utf-8"))
    annotation_ids: dict[int, list[int]] = defaultdict(list)
    for annotation in payload.get("annotations", []):
        annotation_ids[int(annotation["image_id"])].append(int(annotation["id"]))

    rows: list[dict[str, str]] = []
    for source in staging_rows:
        image_id = int(source["source_image_id"])
        suggested_label = source["proposed_condition"].strip()
        row = {field: "" for field in REVIEW_FIELDS}
        row.update(
            {
                "review_id": f"seaclear-v1-review-{image_id:06d}",
                "image_id": str(image_id),
                "image_path_or_relative_key": source["relative_path"],
                "image_sha256": source["sha256"].lower(),
                "source_dataset": "SeaClear v1",
                "source_site": source["site"],
                "source_camera_or_group": source["source_group"],
                "source_annotation_ids": ";".join(map(str, sorted(annotation_ids.get(image_id, [])))),
                "source_category_names": source["category_names"],
                "suggested_model1_domain": source["proposed_domain"],
                "suggested_model1_label": suggested_label,
                "suggestion_confidence": _confidence(suggested_label),
                "review_status": "pending_review",
                "approved_for_training": "false",
                "approved_for_validation": "false",
                "approved_for_test": "false",
            }
        )
        rows.append(row)
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    schema_path = Path(schema_json)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(review_schema(), indent=2) + "\n", encoding="utf-8")
    report = validate_review_queue(output_path, require_all_pending=True)
    report["source_annotation_ids"] = sum(len(value) for value in annotation_ids.values())
    return report


def _complete_review(row: dict[str, str], prefix: str) -> bool:
    return all(row[f"{prefix}_{field}"].strip() for field in ("id", "domain", "label", "timestamp"))


def validate_review_queue(path: str | Path, *, require_all_pending: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = set(REVIEW_FIELDS) - set(reader.fieldnames or ())
        if missing:
            return {"valid": False, "rows": 0, "errors": [f"missing fields: {sorted(missing)}"]}
        rows = list(reader)
    for unique_field in ("review_id", "image_id", "image_path_or_relative_key", "image_sha256"):
        values = [row[unique_field].strip() for row in rows]
        if any(not value for value in values) or len(values) != len(set(values)):
            errors.append(f"{unique_field} must be non-empty and unique")
    for index, row in enumerate(rows, start=2):
        prefix = f"row {index} ({row['review_id']})"
        status = row["review_status"]
        if status not in STATUS_VALUES:
            errors.append(f"{prefix}: invalid review_status")
            continue
        if row["suggested_model1_domain"] not in ("", *DOMAIN_LABELS):
            errors.append(f"{prefix}: invalid suggested domain")
        if row["suggested_model1_label"] not in ("", *CONDITION_LABELS):
            errors.append(f"{prefix}: invalid suggested label")
        if row["suggestion_confidence"] not in CONFIDENCE_VALUES:
            errors.append(f"{prefix}: invalid suggestion confidence")
        if not re.fullmatch(r"[0-9a-f]{64}", row["image_sha256"]):
            errors.append(f"{prefix}: invalid image SHA-256")
        for field in ("reviewer_1_timestamp", "reviewer_2_timestamp", "adjudication_timestamp"):
            if row[field] and not TIMESTAMP_PATTERN.fullmatch(row[field]):
                errors.append(f"{prefix}: invalid {field}")
        approvals = [row[field] for field in ("approved_for_training", "approved_for_validation", "approved_for_test")]
        if any(value not in {"false", "true"} for value in approvals):
            errors.append(f"{prefix}: approval flags must be true or false")
        reviewer_1_complete = _complete_review(row, "reviewer_1")
        reviewer_2_complete = _complete_review(row, "reviewer_2")
        if reviewer_1_complete and reviewer_2_complete and row["reviewer_1_id"] == row["reviewer_2_id"]:
            errors.append(f"{prefix}: reviewers must be distinct")
        for reviewer in ("reviewer_1", "reviewer_2"):
            if row[f"{reviewer}_label"] == "unknown" and not row[f"{reviewer}_notes"].strip():
                errors.append(f"{prefix}: unknown reviewer decision requires notes")
        if status == "pending_review":
            if "true" in approvals or any(row[field] for field in ("adjudicator_id", "adjudicated_domain", "adjudicated_label", "adjudication_timestamp")):
                errors.append(f"{prefix}: pending row carries approval/adjudication data")
        elif status == "needs_adjudication":
            if not reviewer_1_complete or not reviewer_2_complete or "true" in approvals:
                errors.append(f"{prefix}: adjudication row requires two reviews and no approvals")
            if row["reviewer_1_domain"] == row["reviewer_2_domain"] and row["reviewer_1_label"] == row["reviewer_2_label"]:
                errors.append(f"{prefix}: matching reviews do not need adjudication")
        elif status == "rejected":
            if row["rejection_reason"] not in REJECTION_REASONS or "true" in approvals:
                errors.append(f"{prefix}: rejected row requires reason and no approvals")
        elif status == "approved":
            if not reviewer_1_complete or not reviewer_2_complete or "true" not in approvals:
                errors.append(f"{prefix}: approved row requires two reviews and an explicit use approval")
            disagreement = row["reviewer_1_domain"] != row["reviewer_2_domain"] or row["reviewer_1_label"] != row["reviewer_2_label"]
            if disagreement:
                adjudication = all(row[field].strip() for field in (
                    "adjudicator_id", "adjudicated_domain", "adjudicated_label",
                    "adjudicator_notes", "adjudication_timestamp",
                ))
                if not adjudication or row["adjudicator_id"] in {row["reviewer_1_id"], row["reviewer_2_id"]}:
                    errors.append(f"{prefix}: disagreed approval requires independent complete adjudication")
    statuses = Counter(row["review_status"] for row in rows)
    if require_all_pending and statuses != Counter({"pending_review": len(rows)}):
        errors.append("initial queue must contain only pending_review rows")
    return {
        "valid": not errors,
        "rows": len(rows),
        "errors": errors,
        "status_counts": dict(sorted(statuses.items())),
        "approved_use_flags": sum(
            row[field] == "true"
            for row in rows
            for field in ("approved_for_training", "approved_for_validation", "approved_for_test")
        ),
    }
