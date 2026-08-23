from __future__ import annotations

import argparse
import json
from pathlib import Path


def difference_hash(path: Path, size: int = 8) -> int:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install Pillow to detect near duplicates") from exc
    with Image.open(path) as image:
        pixels = list(image.convert("L").resize((size + 1, size)).getdata())
    value = 0
    for row in range(size):
        for column in range(size):
            left = pixels[row * (size + 1) + column]
            right = pixels[row * (size + 1) + column + 1]
            value = (value << 1) | int(left > right)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Report perceptual near-duplicates without deleting files")
    parser.add_argument("input_dir")
    parser.add_argument("--threshold", type=int, default=5)
    parser.add_argument("--output", default="outputs/dataset_audit/near_duplicates.json")
    args = parser.parse_args()
    images = [path for path in Path(args.input_dir).rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    hashes = [(path, difference_hash(path)) for path in sorted(images)]
    pairs = [{"a": str(a), "b": str(b), "hamming_distance": (ha ^ hb).bit_count()}
             for index, (a, ha) in enumerate(hashes) for b, hb in hashes[index + 1:]
             if (ha ^ hb).bit_count() <= args.threshold]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"threshold": args.threshold, "pairs": pairs}, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
