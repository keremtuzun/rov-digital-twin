import json

import pytest

from rov_dt.physical_evidence import audit_dossier


def test_empty_dossier_never_passes(tmp_path):
    path = tmp_path / "dossier.json"
    path.write_text(json.dumps({"stage_records": []}))
    result = audit_dossier(path)
    assert not result["dossier_complete"]
    assert not result["deployment_authorized"]
    assert not result["physical_tests_performed_by_this_audit"]
    assert len(result["stages"]) == 9


def test_unsafe_files_simulation_and_missing_limits_rejected(tmp_path):
    path = tmp_path / "dossier.json"
    path.write_text(json.dumps({"stage_records": [{"stage": "hil",
        "evidence_origin": "simulation", "evidence_files": [{"path": "../outside"}]}]}))
    errors = audit_dossier(path)["stages"][3]["errors"]
    assert "missing or unsafe evidence path" in errors
    assert any("physical hardware" in e for e in errors)
    assert any("acceptance limits" in e for e in errors)


def test_unknown_stage_rejected(tmp_path):
    path = tmp_path / "dossier.json"
    path.write_text(json.dumps({"stage_records": [{"stage": "auto_approved"}]}))
    with pytest.raises(ValueError, match="unknown"):
        audit_dossier(path)
