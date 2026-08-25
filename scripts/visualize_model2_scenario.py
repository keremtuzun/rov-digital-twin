from __future__ import annotations

import argparse
from pathlib import Path

from oceansense.model2.visualization import visualize_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Render debug views for one Failure Twin v0 scenario")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/model2_debug_plots"))
    args = parser.parse_args()
    paths = visualize_scenario(args.scenario, args.output)
    print(f"Wrote {len(paths)} debug plots to {args.output}")


if __name__ == "__main__":
    main()
