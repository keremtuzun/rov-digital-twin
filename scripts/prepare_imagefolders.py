from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from oceansense.data import read_labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize domain and condition ImageFolder trees")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", default="dataset/imagefolders")
    parser.add_argument("--mode", choices=("copy", "hardlink"), default="copy")
    args = parser.parse_args()

    labels_path = Path(args.labels)
    output = Path(args.output)
    records = read_labels(labels_path)
    for record in records:
        if record.split not in {"train", "val", "test"}:
            raise ValueError(f"sample {record.sample_id} has no valid split")
        source = Path(record.file_path)
        if not source.is_absolute():
            source = labels_path.parent / source
        if not source.is_file():
            raise FileNotFoundError(source)
        suffix = source.suffix.lower() or ".jpg"
        targets = [
            output / "domain" / record.split / record.inspection_domain / f"{record.sample_id}{suffix}",
            output / "condition" / record.split / record.primary_label / f"{record.sample_id}{suffix}",
        ]
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError(f"refusing to overwrite {target}")
            if args.mode == "hardlink":
                os.link(source, target)
            else:
                shutil.copy2(source, target)
    print(f"Prepared {len(records)} records under {output}")


if __name__ == "__main__":
    main()
