from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from oceansense.taxonomy import canonicalize_label


def convert_csv(source: str | Path, output: str | Path) -> dict[str, int]:
    with Path(source).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "primary_label" not in reader.fieldnames:
            raise ValueError("annotation CSV requires primary_label")
        rows = list(reader)
        fields = reader.fieldnames
    migrations: dict[str, int] = {}
    for row in rows:
        old = row["primary_label"].strip()
        new = canonicalize_label(old)
        row["primary_label"] = new
        if old != new:
            migrations[f"{old}->{new}"] = migrations.get(f"{old}->{new}", 0) + 1
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return migrations


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy CSV labels to the canonical cautious taxonomy")
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    migrations = convert_csv(args.input, args.output)
    report = Path(args.report or str(Path(args.output).with_suffix(".migration.json")))
    report.write_text(json.dumps({"migrations": migrations}, indent=2), encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
