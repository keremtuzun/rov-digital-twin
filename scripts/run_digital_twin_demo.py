from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from oceansense.digital_twin_demo import run_demo


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the navigation/visual-fixture interface demo (not Model 2)"
    )
    parser.add_argument("--navigation-config", type=Path,
                        default=Path("configs/navigation_twin/demo_mission.json"))
    parser.add_argument("--failure-config", type=Path,
                        default=Path("configs/failure_twin/demo_scenario.json"))
    parser.add_argument("--run-id", default="digital-twin-demo-v1")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--operator", default="manual-demo-command")
    args = parser.parse_args()
    output = args.output or Path("experiments/runs") / args.run_id
    run_demo(
        navigation_config_path=args.navigation_config,
        failure_config_path=args.failure_config,
        output_dir=output,
        run_id=args.run_id,
        git_commit=_git("rev-parse", "HEAD"),
        branch=_git("branch", "--show-current"),
        operator_or_agent=args.operator,
    )
    print(f"Digital twin demo artifacts written to {output}")


if __name__ == "__main__":
    main()
