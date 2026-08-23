from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from .schemas import CONDITION_LABELS, DOMAIN_LABELS, VISIBILITY_LEVELS
from .taxonomy import canonicalize_label, is_domain_compatible

REQUIRED_COLUMNS = {
    "sample_id", "file_path", "source", "license", "split", "inspection_domain", "primary_label",
    "secondary_labels", "contains_anomaly", "condition_status", "risk_level", "weak_point_present",
    "visibility_level", "confidence_label", "synthetic", "mission_or_video_id", "notes",
}


def _parse_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{name} must be true or false")
    return normalized == "true"


@dataclass(frozen=True)
class ImageRecord:
    sample_id: str
    file_path: str
    source: str
    license: str
    split: str
    inspection_domain: str
    primary_label: str
    secondary_labels: str
    contains_anomaly: bool
    condition_status: str
    risk_level: str
    weak_point_present: bool
    visibility_level: str
    confidence_label: str
    synthetic: bool
    mission_or_video_id: str
    notes: str = ""

    @classmethod
    def from_row(cls, row: dict[str, str]) -> ImageRecord:
        missing = REQUIRED_COLUMNS - row.keys()
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        if row["inspection_domain"] not in DOMAIN_LABELS:
            raise ValueError(f"unsupported inspection_domain: {row['inspection_domain']}")
        primary_label = canonicalize_label(row["primary_label"])
        if primary_label not in CONDITION_LABELS:
            raise ValueError(f"unsupported primary_label: {row['primary_label']}")
        if not is_domain_compatible(row["inspection_domain"], primary_label):
            raise ValueError(f"label {primary_label} is incompatible with domain {row['inspection_domain']}")
        if row["visibility_level"] not in VISIBILITY_LEVELS:
            raise ValueError(f"unsupported visibility_level: {row['visibility_level']}")
        if row["split"] not in {"", "train", "val", "test"}:
            raise ValueError(f"unsupported split: {row['split']}")
        if row["confidence_label"] not in {"low", "medium", "high"}:
            raise ValueError("confidence_label must be low, medium, or high")
        if row["condition_status"] not in {"ok", "needs_review", "unsafe_to_conclude", "unknown"}:
            raise ValueError("unsupported condition_status")
        if row["risk_level"] not in {"low", "medium", "high"}:
            raise ValueError("unsupported risk_level")
        for name in ("sample_id", "file_path", "source", "license"):
            if not row[name].strip():
                raise ValueError(f"{name} cannot be empty")
        secondary = {canonicalize_label(item.strip()) for item in re.split(r"[;,|]", row["secondary_labels"]) if item.strip()}
        if secondary - CONDITION_LABELS:
            raise ValueError(f"unsupported secondary_labels: {sorted(secondary - CONDITION_LABELS)}")
        return cls(
            sample_id=row["sample_id"].strip(), file_path=row["file_path"].strip(),
            source=row["source"].strip(), license=row["license"].strip(), split=row["split"].strip(),
            inspection_domain=row["inspection_domain"], primary_label=primary_label,
            secondary_labels=";".join(sorted(secondary)), contains_anomaly=_parse_bool(row["contains_anomaly"], "contains_anomaly"),
            condition_status=row["condition_status"], risk_level=row["risk_level"],
            weak_point_present=_parse_bool(row["weak_point_present"], "weak_point_present"),
            visibility_level=row["visibility_level"], confidence_label=row["confidence_label"],
            synthetic=_parse_bool(row["synthetic"], "synthetic"),
            mission_or_video_id=row.get("mission_or_video_id", "").strip() or row["sample_id"].strip(), notes=row["notes"],
        )

    def to_row(self) -> dict[str, str]:
        values = self.__dict__.copy()
        values["contains_anomaly"] = str(self.contains_anomaly).lower()
        values["weak_point_present"] = str(self.weak_point_present).lower()
        values["synthetic"] = str(self.synthetic).lower()
        return values


def read_labels(path: str | Path) -> list[ImageRecord]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or REQUIRED_COLUMNS - set(reader.fieldnames):
            raise ValueError(f"labels.csv must contain {sorted(REQUIRED_COLUMNS)}")
        records = [ImageRecord.from_row(row) for row in reader]
    ids = [record.sample_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("sample_id values must be unique")
    return records


def validate_dataset(labels_path: str | Path, boxes_path: str | Path | None = None, check_files: bool = True) -> dict:
    labels_path = Path(labels_path)
    records = read_labels(labels_path)
    errors: list[str] = []
    if check_files:
        for record in records:
            candidate = Path(record.file_path)
            if not candidate.is_absolute():
                candidate = labels_path.parent / candidate
            if not candidate.is_file():
                errors.append(f"missing image: {record.sample_id} -> {record.file_path}")
    box_samples: set[str] = set()
    if boxes_path:
        payload = json.loads(Path(boxes_path).read_text(encoding="utf-8"))
        known = {record.sample_id for record in records}
        entries = payload if isinstance(payload, list) else payload.get("annotations", [])
        for entry in entries:
            sample_id = entry.get("sample_id", "")
            if sample_id not in known:
                errors.append(f"bbox references unknown sample: {sample_id}")
            box_samples.add(sample_id)
            for box in entry.get("boxes", []):
                if box.get("label") not in {
                    "possible_weak_point", "inspection_concern", "possible_damage_region", "debris_object",
                    "biofouling_region", "coral_stress_region", "turbidity_region", "net_damage_region", "fish_group",
                }:
                    errors.append(f"unsupported bbox label for {sample_id}")
                if box.get("x_min", -1) < 0 or box.get("y_min", -1) < 0 or box.get("x_max", 0) <= box.get("x_min", 0) or box.get("y_max", 0) <= box.get("y_min", 0):
                    errors.append(f"invalid bbox coordinates for {sample_id}")
        for record in records:
            if record.weak_point_present and record.sample_id not in box_samples:
                errors.append(f"weak_point_present without bbox: {record.sample_id}")
    return {
        "valid": not errors,
        "rows": len(records),
        "errors": errors,
        "class_distribution": dict(sorted(Counter(record.primary_label for record in records).items())),
        "domain_distribution": dict(sorted(Counter(record.inspection_domain for record in records).items())),
        "origin_distribution": dict(sorted(Counter("synthetic" if record.synthetic else "real" for record in records).items())),
        "split_distribution": dict(sorted(Counter(record.split or "unassigned" for record in records).items())),
    }


def stratified_split(records: list[ImageRecord], seed: int = 42) -> list[ImageRecord]:
    """Deterministic group-aware split; a mission/video can occur in only one split."""
    rng = random.Random(seed)
    groups: dict[str, list[ImageRecord]] = defaultdict(list)
    for record in records:
        groups[f"{record.inspection_domain}:{record.primary_label}"].append(record)
    output: list[ImageRecord] = []
    for stratum in groups.values():
        mission_groups: dict[str, list[ImageRecord]] = defaultdict(list)
        for record in stratum:
            mission_groups[record.mission_or_video_id].append(record)
        units = list(mission_groups.values())
        rng.shuffle(units)
        count = len(stratum)
        assigned = 0
        train_target = max(1, round(count * 0.70))
        val_target = train_target + max(1 if count >= 3 else 0, round(count * 0.15))
        for unit in units:
            split = "train" if assigned < train_target else ("val" if assigned < val_target else "test")
            output.extend(replace(record, split=split) for record in unit)
            assigned += len(unit)
    return sorted(output, key=lambda item: item.sample_id)


def write_labels(records: list[ImageRecord], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ImageRecord.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.to_row() for record in records)
    return path
