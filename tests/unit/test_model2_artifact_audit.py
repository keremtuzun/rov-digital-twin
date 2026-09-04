import json
import runpy
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
audit = runpy.run_path(str(ROOT / "scripts/validate_model2_baseline_artifacts.py"))["audit"]


def test_all_saved_baseline_artifacts_agree():
    result = audit(ROOT)
    assert result["valid"] is True
    assert result["held_out_inference_rerun"] is False
    assert len(result["verified_runs"]) == 12


def test_audit_rejects_modified_saved_metrics(tmp_path):
    for relative in ("configs/model2", "data/model2", "reports/model2"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    path = (
        tmp_path / "reports/model2/s1_learned_baselines/independent_mlp"
        / "seed_2026201/test_metrics.json"
    )
    payload = json.loads(path.read_text())
    payload["mae_overall"] = 0.0
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="saved metric differs"):
        audit(tmp_path)
