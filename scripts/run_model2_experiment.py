from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model2_reasoning import EvidenceObservation, StructuralRelation, run_ablation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the claim-bounded Model 2 reasoning ablation")
    parser.add_argument("input", type=Path)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    observations = [EvidenceObservation(**item) for item in payload.get("observations", [])]
    relations = [StructuralRelation(**item) for item in payload.get("relations", [])]
    result = run_ablation(args.target_id, observations, relations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote Model 2 hypothesis and ablations to {args.output}")


if __name__ == "__main__":
    main()
