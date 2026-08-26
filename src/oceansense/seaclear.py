"""Deterministic staging-manifest tooling for the openly licensed SeaClear dataset."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SOURCE_FIELDS = (
    "asset_id",
    "source_image_id",
    "relative_path",
    "site",
    "camera",
    "source_group",
    "width",
    "height",
    "sha256",
    "annotation_count",
    "category_ids",
    "category_names",
    "proposed_domain",
    "proposed_condition",
    "mapping_status",
    "approval_status",
)

NATURAL_CATEGORIES = {
    "plant",
    "animal_etc",
    "animal_sponge",
    "animal_shells",
    "animal_urchin",
    "animal_fish",
    "animal_starfish",
    "branch_wood",
}
ROV_OR_UNKNOWN_CATEGORIES = {
    "unknown_instance",
    "rov_cable",
    "rov_tortuga",
    "rov_vehicle_leg",
    "rov_bluerov",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _proposal(category_names: set[str]) -> tuple[str, str]:
    debris = category_names - NATURAL_CATEGORIES - ROV_OR_UNKNOWN_CATEGORIES
    if debris:
        return "contamination", "marine_debris"
    if any(name.startswith("animal_") for name in category_names):
        return "nature_ecology", "fish_or_habitat_activity"
    if category_names & NATURAL_CATEGORIES:
        return "nature_ecology", ""
    return "unknown", "unknown"


def build_source_manifest(
    extracted_root: str | Path,
    output_csv: str | Path,
    summary_json: str | Path,
) -> dict[str, Any]:
    """Build a non-approved staging manifest from COCO metadata and local image hashes."""
    root = Path(extracted_root).resolve()
    coco_path = root / "dataset.json"
    if not coco_path.is_file():
        raise FileNotFoundError(f"missing SeaClear COCO metadata: {coco_path}")
    payload = json.loads(coco_path.read_text(encoding="utf-8"))
    images = payload.get("images", [])
    annotations = payload.get("annotations", [])
    categories = {int(row["id"]): str(row["name"]) for row in payload.get("categories", [])}

    files_by_basename: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(root.rglob("*.jpg")):
        files_by_basename[path.name].append(path)
    duplicate_basenames = sorted(name for name, paths in files_by_basename.items() if len(paths) != 1)
    if duplicate_basenames:
        raise ValueError(f"SeaClear image basenames are not unique: {duplicate_basenames[:5]}")

    annotations_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for annotation in annotations:
        annotations_by_image[int(annotation["image_id"])].append(annotation)

    rows: list[dict[str, str]] = []
    missing: list[str] = []
    for image in sorted(images, key=lambda row: int(row["id"])):
        image_id = int(image["id"])
        basename = Path(str(image["file_name"])).name
        candidates = files_by_basename.get(basename, [])
        if len(candidates) != 1:
            missing.append(basename)
            continue
        path = candidates[0]
        relative = path.relative_to(root)
        if len(relative.parts) != 3:
            raise ValueError(f"unexpected SeaClear site/camera layout: {relative.as_posix()}")
        site, camera, _ = relative.parts
        image_annotations = annotations_by_image.get(image_id, [])
        category_ids = sorted({int(item["category_id"]) for item in image_annotations})
        unknown_ids = [category_id for category_id in category_ids if category_id not in categories]
        if unknown_ids:
            raise ValueError(f"image {image_id} references unknown categories: {unknown_ids}")
        category_names = {categories[category_id] for category_id in category_ids}
        proposed_domain, proposed_condition = _proposal(category_names)
        rows.append(
            {
                "asset_id": f"seaclear-v1-{image_id:06d}",
                "source_image_id": str(image_id),
                "relative_path": relative.as_posix(),
                "site": site,
                "camera": camera,
                "source_group": f"{site}/{camera}",
                "width": str(int(image["width"])),
                "height": str(int(image["height"])),
                "sha256": _sha256(path),
                "annotation_count": str(len(image_annotations)),
                "category_ids": ";".join(map(str, category_ids)),
                "category_names": ";".join(sorted(category_names)),
                "proposed_domain": proposed_domain,
                "proposed_condition": proposed_condition,
                "mapping_status": "annotation_proposal_requires_image_review",
                "approval_status": "pending_review",
            }
        )
    if missing:
        raise ValueError(f"COCO records without exactly one local image: {missing[:5]}")
    if len(rows) != len(images) or len({row["asset_id"] for row in rows}) != len(rows):
        raise ValueError("SeaClear source manifest is incomplete or contains duplicate asset IDs")

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    summary: dict[str, Any] = {
        "status": "STAGING_ONLY_NOT_APPROVED_FOR_TRAINING",
        "source": "SeaClear v1",
        "rows": len(rows),
        "annotations": len(annotations),
        "categories": len(categories),
        "site_counts": dict(sorted(Counter(row["site"] for row in rows).items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "proposed_condition_counts": dict(
            sorted(Counter(row["proposed_condition"] or "review_required" for row in rows).items())
        ),
        "all_assets_hashed": all(len(row["sha256"]) == 64 for row in rows),
        "approval_status": "pending_review",
    }
    summary_path = Path(summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
