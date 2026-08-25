"""Fail-closed configuration and dataset gates for the new Model 1 v2 baseline."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .data import read_labels
from .governance import audit_manifest

BASELINE_ID = "model1_baseline_v2"
DOMAIN_LABELS_V2 = (
    "structure",
    "nature_ecology",
    "contamination",
    "fishing_aquaculture",
    "general_underwater",
    "unknown",
)
CONDITION_LABELS_V2 = (
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


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_baseline_config(path: str | Path) -> dict[str, Any]:
    """Load JSON-compatible YAML without making PyYAML a core dependency."""
    config_path = Path(path)
    raw = config_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError as exc:
            raise ValueError("config must be JSON-compatible YAML or PyYAML must be installed") from exc
        payload = yaml.safe_load(raw)
    if not isinstance(payload, dict):
        raise ValueError("baseline config must contain a mapping")
    validate_baseline_config(payload)
    return payload


def validate_baseline_config(config: dict[str, Any]) -> None:
    if config.get("model_version") != BASELINE_ID:
        raise ValueError(f"model_version must be {BASELINE_ID}")
    if config.get("architecture") != "efficientnet_b0":
        raise ValueError("Model 1 v2 architecture is locked to efficientnet_b0")
    activation = config.get("activation", {})
    if activation.get("requires_recorded_authorization") is not True:
        raise ValueError("Model 1 v2 requires recorded activation authorization")
    if not activation.get("approval_file") or not activation.get("allowed_reasons"):
        raise ValueError("activation approval file and allowed reasons are required")
    labels = config.get("labels", {})
    if tuple(labels.get("domain", ())) != DOMAIN_LABELS_V2:
        raise ValueError("domain label order does not match the locked v2 schema")
    if tuple(labels.get("condition", ())) != CONDITION_LABELS_V2:
        raise ValueError("condition label order does not match the locked v2 schema")
    training = config.get("training", {})
    required_training = {
        "weights": "imagenet",
        "augmentation": "underwater_physical_aug_v1",
        "class_balance": "weighted_loss",
        "optimizer": "adamw",
        "selection_metric": "validation_macro_f1",
        "precision": "float32",
        "seed": 42,
    }
    mismatches = {
        key: (training.get(key), expected)
        for key, expected in required_training.items()
        if training.get(key) != expected
    }
    if mismatches:
        raise ValueError(f"locked training contract mismatch: {mismatches}")
    if training.get("warmup_epochs", 0) < 1 or training.get("maximum_epochs", 0) < 1:
        raise ValueError("warmup_epochs and maximum_epochs must be positive")
    if not 0.0 < float(training.get("augmentation_probability", 0)) <= 1.0:
        raise ValueError("augmentation_probability must be in (0, 1]")
    artifacts = config.get("artifacts", {})
    for task in ("domain", "condition"):
        checkpoint = str(artifacts.get(task, {}).get("checkpoint", ""))
        if BASELINE_ID not in checkpoint or not checkpoint.endswith(".pt"):
            raise ValueError(f"{task} checkpoint path must use the v2 identity")
        if "oceansense_domain_efficientnet_b0.pt" in checkpoint or "oceansense_condition_efficientnet_b0.pt" in checkpoint:
            raise ValueError("v2 must never overwrite an original Model 1 checkpoint path")


def _resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def _read_split(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"sample_id", "split", "mission_or_video_id"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"split.csv missing columns: {sorted(missing)}")
        rows = {}
        for row in reader:
            sample_id = row["sample_id"].strip()
            if not sample_id or sample_id in rows:
                raise ValueError("split.csv sample_id values must be non-empty and unique")
            if row["split"] not in {"train", "val", "test"}:
                raise ValueError(f"invalid split for {sample_id}: {row['split']}")
            rows[sample_id] = {key: value.strip() for key, value in row.items()}
    return rows


def _read_checksums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(f"invalid checksums.sha256 line {line_number}")
        name = parts[1].lstrip("* ").replace("\\", "/")
        entries[name] = parts[0].lower()
    return entries


def _recorded_checksum(entries: dict[str, str], filename: str) -> str | None:
    matches = [
        digest
        for name, digest in entries.items()
        if name == filename or name.endswith(f"/{filename}")
    ]
    return matches[0] if len(matches) == 1 else None


def dataset_preflight(config_path: str | Path, *, check_images: bool = True) -> dict[str, Any]:
    """Return a complete, non-mutating readiness report; never weakens a failed gate."""
    config_path = Path(config_path).resolve()
    config = load_baseline_config(config_path)
    repo_root = config_path.parent.parent
    data = config["data"]
    paths = {
        name: _resolve(repo_root, data[name])
        for name in ("root", "manifest", "labels", "split", "checksums")
    }
    approval_path = _resolve(repo_root, config["activation"]["approval_file"])
    errors: list[str] = []
    hashes: dict[str, str] = {"config": sha256_file(config_path)}
    for name, path in paths.items():
        if name == "root":
            if not path.is_dir():
                errors.append(f"missing dataset root: {path}")
        elif not path.is_file():
            errors.append(f"missing required file: {path}")
        else:
            hashes[name] = sha256_file(path)
    for value in data.get("required_evidence", []):
        evidence = _resolve(repo_root, value)
        if not evidence.exists() or (evidence.is_dir() and not any(evidence.iterdir())):
            errors.append(f"missing or empty evidence: {evidence}")
    if not approval_path.is_file():
        errors.append(f"missing activation approval: {approval_path}")
    if errors:
        return {"ready": False, "model_version": BASELINE_ID, "errors": errors, "hashes": hashes}

    try:
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"invalid activation approval: {exc}")
        approval = {}
    if approval.get("model_version") != BASELINE_ID or approval.get("decision") != "AUTHORIZED":
        errors.append("activation approval must authorize model1_baseline_v2")
    if approval.get("reason") not in config["activation"]["allowed_reasons"]:
        errors.append("activation approval reason is missing or unsupported")
    if approval.get("original_model_status") != "BLOCKED_NOT_FROZEN":
        errors.append("activation approval must preserve original Model 1 as BLOCKED_NOT_FROZEN")
    if not approval.get("authorized_by") or not approval.get("authorized_at"):
        errors.append("activation approval requires authorized_by and authorized_at")

    checksum_entries = _read_checksums(paths["checksums"])
    for name in ("manifest", "labels", "split"):
        expected = _recorded_checksum(checksum_entries, paths[name].name)
        if expected is None:
            errors.append(f"checksums.sha256 must contain exactly one entry for {paths[name].name}")
        elif expected != hashes[name]:
            errors.append(f"checksum mismatch for {paths[name].name}")

    approved, rejected = audit_manifest(paths["manifest"])
    if rejected:
        errors.append(f"manifest contains {len(rejected)} unapproved/rejected assets")
    approved_ids = {row["sample_id"] for row in approved}
    records = read_labels(paths["labels"])
    split_rows = _read_split(paths["split"])
    record_ids = {record.sample_id for record in records}
    if record_ids != set(split_rows):
        errors.append("labels.csv and split.csv sample IDs do not match exactly")
    missing_approvals = sorted(record_ids - approved_ids)
    if missing_approvals:
        errors.append(f"labels reference {len(missing_approvals)} assets without approval")

    groups: dict[str, set[str]] = defaultdict(set)
    condition_counts: Counter[tuple[str, str]] = Counter()
    domain_counts: Counter[tuple[str, str]] = Counter()
    for record in records:
        split_row = split_rows.get(record.sample_id)
        if split_row and (split_row["split"] != record.split or split_row["mission_or_video_id"] != record.mission_or_video_id):
            errors.append(f"split contract mismatch for {record.sample_id}")
        groups[record.mission_or_video_id].add(record.split)
        condition_counts[(record.split, record.primary_label)] += 1
        domain_counts[(record.split, record.inspection_domain)] += 1
        if data.get("require_real_test") and record.split == "test" and record.synthetic:
            errors.append(f"synthetic sample in primary test split: {record.sample_id}")
        if check_images:
            image = Path(record.file_path)
            if not image.is_absolute():
                image = paths["labels"].parent / image
            if not image.is_file():
                errors.append(f"missing image: {record.sample_id} -> {record.file_path}")
    leaked_groups = sorted(group for group, splits in groups.items() if len(splits) > 1)
    if leaked_groups:
        errors.append(f"mission/video group leakage across splits: {leaked_groups}")

    floors = data["minimum_per_class"]
    for split in ("train", "val", "test"):
        minimum = int(floors[split])
        for label in CONDITION_LABELS_V2:
            if condition_counts[(split, label)] < minimum:
                errors.append(f"condition floor not met: {split}/{label} < {minimum}")
        for label in DOMAIN_LABELS_V2:
            if domain_counts[(split, label)] < minimum:
                errors.append(f"domain floor not met: {split}/{label} < {minimum}")

    return {
        "ready": not errors,
        "model_version": BASELINE_ID,
        "errors": errors,
        "hashes": hashes,
        "rows": len(records),
        "approved_manifest_rows": len(approved),
        "condition_counts": {f"{split}:{label}": count for (split, label), count in sorted(condition_counts.items())},
        "domain_counts": {f"{split}:{label}": count for (split, label), count in sorted(domain_counts.items())},
    }
