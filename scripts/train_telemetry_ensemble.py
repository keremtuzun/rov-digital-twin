"""Train seed-diverse telemetry baselines and write an immutable ensemble manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rov_dt.training import train_from_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="41,42,43,44,45")
    parser.add_argument("--epochs", type=int, default=180)
    args = parser.parse_args()
    seeds = [int(value) for value in args.seeds.split(",")]
    if len(set(seeds)) < 2:
        raise ValueError("ensemble training requires at least two unique seeds")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    members = []
    for index, seed in enumerate(seeds, 1):
        model_path = args.output_dir / f"model_{index:02d}.json"
        report_path = args.output_dir / f"model_{index:02d}_metrics.json"
        metrics = train_from_csv(args.input, model_path, report_path, epochs=args.epochs, seed=seed)
        members.append(
            {
                "seed": seed,
                "model": model_path.name,
                "sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                "test_macro_f1": metrics["macro_f1"],
                "calibration_version": "temperature-scaling-v1",
            }
        )
    manifest = {
        "ensemble_version": "telemetry-ensemble-v1",
        "members": members,
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
    }
    (args.output_dir / "ensemble_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
