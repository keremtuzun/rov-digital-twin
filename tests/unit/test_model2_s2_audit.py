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
    assert not result["deployment_authorized"]
    assert not result["uncertainty_calibrated"]
    assert result["full_model_ood_coverage"] == pytest.approx(0.6034166666666666)


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


@pytest.mark.parametrize("tamper", ["inventory", "sources", "coverage", "unobserved", "scope"])
def test_s2_audit_rejects_incomplete_inventory_and_misleading_summary(tmp_path, tamper):
    for relative in ("configs/model2", "data/model2/s2_research", "reports/model2/s2_research_v0",
                     "src/oceansense/model2"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    output = tmp_path / "reports/model2/s2_research_v0"
    name = {"inventory": "full/seed_2026901/completed.json",
            "sources": "environment.json"}.get(tamper, "summary.json")
    path = output / name
    payload = json.loads(path.read_text())
    if tamper == "inventory":
        payload["files"].pop("ood_mean.npy")
    elif tamper == "sources":
        payload["source_sha256"] = {}
    elif tamper == "coverage":
        payload["variants"]["full"]["ood"]["uncertainty"]["empirical_coverage"]["mean"] = 0.99
    elif tamper == "unobserved":
        payload["variants"]["full"]["ood"]["unobserved_mae"]["mean"] = 0
    else:
        payload["synthetic_only"] = False
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="inventory|summary"):
        audit(tmp_path)
