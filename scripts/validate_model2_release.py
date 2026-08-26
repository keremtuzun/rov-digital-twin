"""Validate an immutable Twin 2 / Model 2 dataset release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model2.release_validator import validate_release


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", default="data/model2/d0_debug")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-out")
    parser.add_argument("--require-debug-d0", action="store_true")
    args = parser.parse_args(argv)
    report = validate_release(args.release_dir, require_debug_d0=args.require_debug_d0)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        output = Path(args.json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    if args.strict and not report["valid"]:
        return 2
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
