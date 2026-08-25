from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.experiment import read_run_manifest


def _render(value: object) -> str:
    return "```json\n" + json.dumps(value, indent=2, sort_keys=True) + "\n```"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an evidence-bounded Markdown run report")
    parser.add_argument("run_manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = read_run_manifest(args.run_manifest)
    sections = [
        f"# Run report: {manifest.run_id}",
        "## Identity",
        _render({"date": manifest.date, "git_commit": manifest.git_commit,
                 "branch": manifest.branch, "track": manifest.track,
                 "operator_or_agent": manifest.operator_or_agent}),
        "## Reproduction inputs", _render({"config_path": manifest.config_path,
                                             "dataset_manifest": manifest.dataset_manifest,
                                             "prototype": manifest.checkpoint_or_prototype_version,
                                             "inputs": manifest.inputs}),
        "## Outputs", _render(manifest.outputs),
        "## Metrics", _render(manifest.metrics),
        "## Evidence type", manifest.synthetic_or_real_or_mixed,
        "## Limitations", "\n".join(f"- {item}" for item in manifest.limitations),
        "## Next actions", "\n".join(f"- {item}" for item in manifest.next_actions),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
