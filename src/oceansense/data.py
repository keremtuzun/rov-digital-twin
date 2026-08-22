from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from .schemas import ALLOWED_LABELS, VISIBILITY_LEVELS


REQUIRED_COLUMNS = {
    "sample_id", "file_path", "source", "license", "split", "primary_label",
    "contains_anomaly", "weak_point_present", "visibility_level", "confidence_label", "notes",
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
    primary_label: str
    contains_anomaly: bool
    weak_point_present: bool
    visibility_level: str
    confidence_label: str
    notes: str = ""

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "ImageRecord":
        missing = REQUIRED_COLUMNS - row.keys()
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        if row["primary_label"] not in ALLOWED_LABELS:
            raise ValueError(f"unsupported primary_label: {row['primary_label']}")
        if row["visibility_level"] not in VISIBILITY_LEVELS:
            raise ValueError(f"unsupported visibility_level: {row['visibility_level']}")
        if row["split"] not in {"", "train", "val", "test"}:
            raise ValueError(f"unsupported split: {row['split']}")
        if row["confidence_label"] not in {"low", "medium", "high"}:
            raise ValueError("confidence_label must be low, medium, or high")
        return cls(
            sample_id=row["sample_id"].strip(), file_path=row["file_path"].strip(),
            source=row["source"].strip(), license=row["license"].strip(), split=row["split"].strip(),
            primary_label=row["primary_label"], contains_anomaly=_parse_bool(row["contains_anomaly"], "contains_anomaly"),
            weak_point_present=_parse_bool(row["weak_point_present"], "weak_point_present"),
            visibility_level=row["visibility_level"], confidence_label=row["confidence_label"], notes=row["notes"],
        )

    def to_row(self) -> dict[str, str]:
        values = self.__dict__.copy()
        values["contains_anomaly"] = str(self.contains_anomaly).lower()
        values["weak_point_present"] = str(self.weak_point_present).lower()
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
                if box.get("label") not in {"possible_weak_point", "inspection_concern", "possible_damage_region", "debris_object", "biofouling_region"}:
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
        "split_distribution": dict(sorted(Counter(record.split or "unassigned" for record in records).items())),
    }


def stratified_split(records: list[ImageRecord], seed: int = 42) -> list[ImageRecord]:
    """Deterministic 70/15/15 split, stratified by primary label."""
    rng = random.Random(seed)
    groups: dict[str, list[ImageRecord]] = defaultdict(list)
    for record in records:
        groups[record.primary_label].append(record)
    output: list[ImageRecord] = []
    for group in groups.values():
        rng.shuffle(group)
        count = len(group)
        train_end = max(1, round(count * 0.70))
        val_end = min(count, train_end + max(1 if count >= 3 else 0, round(count * 0.15)))
        for index, record in enumerate(group):
            split = "train" if index < train_end else ("val" if index < val_end else "test")
            output.append(replace(record, split=split))
    return sorted(output, key=lambda item: item.sample_id)


def write_labels(records: list[ImageRecord], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ImageRecord.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.to_row() for record in records)
    return path
