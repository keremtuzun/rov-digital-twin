from __future__ import annotations

import argparse
from pathlib import Path

import pypdfium2 as pdfium


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("output_dir")
    parser.add_argument("--scale", type=float, default=1.5)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(args.pdf)
    for index in range(len(pdf)):
        bitmap = pdf[index].render(scale=args.scale)
        bitmap.to_pil().save(output / f"page-{index + 1}.png")
    print(f"Rendered {len(pdf)} pages")


if __name__ == "__main__":
    main()
