from __future__ import annotations

import argparse
import json

from oceansense.governance import audit_manifest, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Route manifest rows through the OceanSense license gate")
    parser.add_argument("manifest")
    parser.add_argument("--approved", default="dataset/manifests/approved_assets.csv")
    parser.add_argument("--rejected", default="dataset/manifests/rejected_assets.csv")
    args = parser.parse_args()
    approved, rejected = audit_manifest(args.manifest)
    write_manifest(args.approved, approved)
    write_manifest(args.rejected, rejected)
    print(json.dumps({"approved": len(approved), "rejected_or_manual_review": len(rejected)}, indent=2))


if __name__ == "__main__":
    main()
