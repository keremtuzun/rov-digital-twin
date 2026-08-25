from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from oceansense.model2.dataset import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Model 2 Failure Twin v0 debug dataset")
    parser.add_argument("--config", type=Path, default=Path("configs/model2/twin_v0.yaml"))
    parser.add_argument("--output", type=Path, default=Path("data/simulated/model2_debug_v0"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Model 2 dataset config must be a YAML mapping")
    manifest = generate_dataset(config, args.output)
    print(
        f"Generated {manifest['scenario_count']} scenario-level Failure Twin v0 fixtures "
        f"at {args.output}"
    )


if __name__ == "__main__":
    main()
