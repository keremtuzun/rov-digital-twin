from __future__ import annotations

import argparse
import json

from oceansense.data import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OceanSense labels and optional boxes")
    parser.add_argument("labels")
    parser.add_argument("--boxes")
    parser.add_argument("--skip-file-check", action="store_true")
    args = parser.parse_args()
    report = validate_dataset(args.labels, args.boxes, check_files=not args.skip_file_check)
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
