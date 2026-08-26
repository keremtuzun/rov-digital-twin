"""Build or validate the fail-closed SeaClear human-review queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.seaclear_review import build_review_queue, validate_review_queue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging-manifest", default="data/model1_baseline_v2/manifests/seaclear_source_assets.csv")
    parser.add_argument("--coco-json", default="data/model1_baseline_v2/raw/seaclear/v1/extracted/dataset.json")
    parser.add_argument("--output", default="data/model1_baseline_v2/manifests/label_review_queue.csv")
    parser.add_argument("--schema", default="data/model1_baseline_v2/manifests/label_review_schema.json")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Replace an existing queue; never use after human review starts")
    args = parser.parse_args()
    output = Path(args.output)
    if args.validate_only:
        report = validate_review_queue(output)
    else:
        if output.exists() and not args.force:
            raise SystemExit(f"refusing to overwrite existing review queue: {output}; use --validate-only")
        report = build_review_queue(args.staging_manifest, args.coco_json, output, args.schema)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["valid"] else 2)


if __name__ == "__main__":
    main()
