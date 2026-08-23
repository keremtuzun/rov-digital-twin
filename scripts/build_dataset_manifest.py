from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from oceansense.governance import read_manifest, sha256_file, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Hash local assets into a resumable raw manifest; never downloads")
    parser.add_argument("input_dir")
    parser.add_argument("--output", default="dataset/manifests/raw_assets.csv")
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--license", required=True)
    parser.add_argument("--license-url", required=True)
    parser.add_argument("--attribution", required=True)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--domain", default="general_underwater")
    parser.add_argument("--label", default="unknown")
    args = parser.parse_args()
    output = Path(args.output)
    existing = read_manifest(output) if output.exists() else []
    by_asset = {row["original_asset_url"]: row for row in existing}
    for path in sorted(Path(args.input_dir).rglob("*")):
        if not path.is_file():
            continue
        uri = path.resolve().as_uri()
        digest = sha256_file(path)
        if uri in by_asset and by_asset[uri].get("sha256") == digest:
            continue
        by_asset[uri] = {
            "sample_id": f"OS-{digest[:16]}", "source_name": args.source_name,
            "source_url": args.source_url, "original_asset_url": uri, "license": args.license,
            "license_url": args.license_url, "attribution": args.attribution,
            "downloaded_at": datetime.now(timezone.utc).isoformat(), "sha256": digest,
            "inspection_domain": args.domain, "primary_label": args.label,
            "annotation_type": "unlabeled", "mission_or_video_id": args.mission,
            "frame_timestamp": "", "real_or_synthetic": "real", "approved_by": "",
            "approval_status": "pending", "notes": "Local file indexed; license audit required",
        }
    write_manifest(output, sorted(by_asset.values(), key=lambda row: row["sample_id"]))
    print(f"Indexed {len(by_asset)} assets in {output}")


if __name__ == "__main__":
    main()
