import hashlib
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
recover_bytes = runpy.run_path(str(ROOT / "scripts/repair_model2_evidence_newlines.py"))[
    "recover_bytes"
]


def test_restore_exact_original_hash_without_replacing_content():
    original = b'{\r\n  "test": true\r\n}\r\n'
    expected = hashlib.sha256(original).hexdigest()
    assert recover_bytes(original.replace(b"\r\n", b"\n"), expected) == original
    assert recover_bytes(original, expected) == original
    with pytest.raises(ValueError, match="refusing repair"):
        recover_bytes(original.replace(b"true", b"false"), expected)
