"""Dataset manifest and license gates with no network or download side effects."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

MANIFEST_FIELDS = (
    "sample_id", "source_name", "source_url", "original_asset_url", "license", "license_url",
    "attribution", "downloaded_at", "sha256", "inspection_domain", "primary_label",
    "annotation_type", "mission_or_video_id", "frame_timestamp", "real_or_synthetic",
    "approved_by", "approval_status", "notes",
)
ALLOWED_LICENSES = {"public domain", "cc0", "cc0-1.0", "cc by 4.0", "cc-by-4.0"}


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = set(MANIFEST_FIELDS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"manifest missing columns: {sorted(missing)}")
        return [{field: row.get(field, "").strip() for field in MANIFEST_FIELDS} for row in reader]


def write_manifest(path: str | Path, rows: list[dict[str, str]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in MANIFEST_FIELDS} for row in rows)
    return output


def license_gate(row: dict[str, str]) -> tuple[bool, str]:
    license_name = row.get("license", "").strip().lower()
    if license_name not in ALLOWED_LICENSES:
        return False, f"license not in automatic allowlist: {row.get('license', '') or 'missing'}"
    if row.get("approval_status", "").lower() != "approved" or not row.get("approved_by", "").strip():
        return False, "explicit approval_status=approved and approved_by are required"
    if len(row.get("sha256", "")) != 64:
        return False, "valid SHA-256 is required"
    if not row.get("source_url", "").startswith(("http://", "https://", "internal://")):
        return False, "source_url is required"
    if not row.get("license_url", "").startswith(("http://", "https://", "internal://")):
        return False, "license_url is required"
    if not row.get("original_asset_url", "").strip() or not row.get("downloaded_at", "").strip():
        return False, "original_asset_url and downloaded_at are required"
    if not row.get("attribution", "").strip():
        return False, "attribution is required"
    return True, "approved by allowlist and explicit reviewer"


def audit_manifest(path: str | Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    approved, rejected = [], []
    for source in read_manifest(path):
        allowed, reason = license_gate(source)
        row = dict(source)
        row["notes"] = "; ".join(filter(None, [row.get("notes", ""), f"license_audit: {reason}"]))
        (approved if allowed else rejected).append(row)
    return approved, rejected
