import json
import runpy
import shutil
from pathlib import Path

import pytest

from oceansense.model2.research_experiment import run_experiment

ROOT = Path(__file__).resolve().parents[2]
audit = runpy.run_path(str(ROOT / "scripts/audit_model2_s2_research.py"))["audit"]


def test_all_s2_evidence_is_consistent():
    result = audit(ROOT)
    assert result["valid"]
    assert result["runs_verified"] == 21
    assert not result["held_out_inference_rerun"]


def test_s2_refuses_repeat_experiment():
    with pytest.raises(FileExistsError, match="refusing"):
        run_experiment(ROOT, ROOT / "configs/model2/s2_research_protocol.json")


def test_s2_audit_rejects_changed_metrics(tmp_path):
    for relative in ("configs/model2", "data/model2/s2_research", "reports/model2/s2_research_v0",
                     "src/oceansense/model2"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    path = tmp_path / "reports/model2/s2_research_v0/full/seed_2026901/test_metrics.json"
    metrics = json.loads(path.read_text())
    metrics["mae_overall"] = 0
    path.write_text(json.dumps(metrics))
    with pytest.raises(ValueError, match="hash mismatch"):
        audit(tmp_path)
