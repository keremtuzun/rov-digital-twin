"""Restore only CRLF/LF-corrupted evidence whose original hash can be proven.

Dry-run by default. No checksums are changed; unrelated content is never repaired.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def recover_bytes(content: bytes, expected: str) -> bytes:
    if hashlib.sha256(content).hexdigest() == expected:
        return content
    lf = content.replace(b"\r\n", b"\n")
    for candidate in (lf, lf.replace(b"\n", b"\r\n")):
        if hashlib.sha256(candidate).hexdigest() == expected:
            return candidate
    raise ValueError("content differs beyond newline conversion; refusing repair")


def repair(root: Path, apply: bool = False) -> list[str]:
    expected = {}
    for manifest in (root / "data/model2").glob("*/checksums.json"):
        for name, digest in json.loads(manifest.read_text())["files"].items():
            if Path(name).name != name:
                raise ValueError("unsafe checksum path")
            expected[manifest.parent / name] = digest
    for manifest in (root / "reports/model2").rglob("selected_checkpoint.json"):
        payload = json.loads(manifest.read_text())
        expected[manifest.parent / "checkpoint.pt"] = payload["checkpoint_sha256"]
        expected[manifest.parent / "config.json"] = payload["config_sha256"]
    changes = {}
    for path, digest in expected.items():
        content = path.read_bytes()
        recovered = recover_bytes(content, digest)
        if recovered != content:
            changes[path] = recovered
    # Validate every candidate before any write, then verify every repaired file.
    if apply:
        for path, recovered in changes.items():
            path.write_bytes(recovered)
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected[path]:
                raise RuntimeError(f"repair readback failed: {path}")
    return [str(path.relative_to(root)) for path in changes]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps({"applied": args.apply,
                      "files": repair(Path(__file__).resolve().parents[1], args.apply)}, indent=2))
