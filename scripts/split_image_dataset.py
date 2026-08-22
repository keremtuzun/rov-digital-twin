from __future__ import annotations

import argparse

from oceansense.data import read_labels, stratified_split, write_labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Create deterministic stratified train/val/test splits")
    parser.add_argument("labels")
    parser.add_argument("--output", default="dataset/processed/labels.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    output = write_labels(stratified_split(read_labels(args.labels), args.seed), args.output)
    print(output)


if __name__ == "__main__":
    main()
