from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dataset import build_llm_instructions, generate_dataset, read_csv, write_csv, write_jsonl
from .decision import SafetyDecisionAgent
from .model import SoftmaxWeakPointClassifier
from .training import train_from_csv


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rovdt", description="ROV digital-twin intelligence CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--rows", type=int, default=4000)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--output", default="data/telemetry.csv")
    train = sub.add_parser("train")
    train.add_argument("--input", default="data/telemetry.csv")
    train.add_argument("--model", default="models/weakpoint.json")
    train.add_argument("--report", default="artifacts/metrics.json")
    train.add_argument("--epochs", type=int, default=180)
    decide = sub.add_parser("decide")
    decide.add_argument("--model", default="models/weakpoint.json")
    decide.add_argument("--input", default="data/telemetry.csv")
    decide.add_argument("--row", type=int, default=0)
    llm = sub.add_parser("build-llm-data")
    llm.add_argument("--input", default="data/telemetry.csv")
    llm.add_argument("--output", default="data/llm_instructions.jsonl")
    llm.add_argument("--limit", type=int, default=1000)
    demo = sub.add_parser("demo")
    demo.add_argument("--output-dir", default="artifacts/demo")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "generate":
        path = write_csv(generate_dataset(args.rows, args.seed), args.output)
        print(json.dumps({"dataset": str(path), "rows": args.rows}))
    elif args.command == "train":
        metrics = train_from_csv(args.input, args.model, args.report, epochs=args.epochs)
        print(json.dumps(metrics, indent=2))
    elif args.command == "decide":
        sample = read_csv(args.input)[args.row]
        result = SafetyDecisionAgent(SoftmaxWeakPointClassifier.load(args.model)).decide(sample)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.command == "build-llm-data":
        records = build_llm_instructions(read_csv(args.input), args.limit)
        path = write_jsonl(records, args.output)
        print(json.dumps({"dataset": str(path), "rows": len(records)}))
    elif args.command == "demo":
        root = Path(args.output_dir)
        dataset = write_csv(generate_dataset(1500, 42), root / "telemetry.csv")
        metrics = train_from_csv(dataset, root / "weakpoint.json", root / "metrics.json", epochs=140)
        samples = read_csv(dataset)
        agent = SafetyDecisionAgent(SoftmaxWeakPointClassifier.load(root / "weakpoint.json"))
        decisions = [agent.decide(sample).to_dict() for sample in samples[:20]]
        (root / "decisions.json").write_text(json.dumps(decisions, indent=2), encoding="utf-8")
        write_jsonl(build_llm_instructions(samples, 250), root / "llm_instructions.jsonl")
        print(json.dumps({"output_dir": str(root), "accuracy": metrics["accuracy"], "macro_f1": metrics["macro_f1"]}, indent=2))


if __name__ == "__main__":
    main()
