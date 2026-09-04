"""Read-only physical-validation dossier checks, never vehicle/deployment authorization."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

STAGES = ("simulation", "recorded_replay", "sil", "hil", "bench", "pool",
          "sheltered_water", "near_shore", "open_water")


def audit_dossier(path: Path) -> dict:
    payload = json.loads(path.read_text())
    records = payload.get("stage_records", [])
    if not isinstance(records, list):
        raise ValueError("stage_records must be a list")
    names = [r.get("stage") for r in records]
    if len(names) != len(set(names)) or set(names) - set(STAGES):
        raise ValueError("unknown or duplicate stage")
    lookup = {r["stage"]: r for r in records}
    results, prior_complete = [], True
    for index, stage in enumerate(STAGES):
        record = lookup.get(stage, {})
        errors = []
        if not prior_complete:
            errors.append("previous stage lacks accepted evidence")
        for key in ("operator", "independent_reviewer", "run_id", "run_timestamp",
                    "vehicle_version", "software_commit", "calibration_version", "risk_review_id"):
            if not record.get(key):
                errors.append(f"missing {key}")
        if record.get("operator") == record.get("independent_reviewer"):
            errors.append("operator and independent reviewer must differ")
        if index >= 3 and record.get("evidence_origin") != "physical_hardware":
            errors.append("physical hardware evidence required; simulation is insufficient")
        if type(record.get("critical_safety_events")) is not int or record["critical_safety_events"] != 0:
            errors.append("unresolved or unreported critical safety events")
        if record.get("independent_review_decision") != "accepted":
            errors.append("independent review has not accepted evidence")
        files = record.get("evidence_files", [])
        if not files:
            errors.append("no raw evidence files")
        for entry in files:
            candidate = (path.parent / entry.get("path", "")).resolve()
            if not candidate.is_relative_to(path.parent.resolve()) or not candidate.is_file():
                errors.append("missing or unsafe evidence path")
            elif hashlib.sha256(candidate.read_bytes()).hexdigest() != entry.get("sha256"):
                errors.append("evidence checksum mismatch")
        metrics = record.get("predeclared_metrics", [])
        if not metrics:
            errors.append("missing predeclared measured acceptance limits")
        for metric in metrics:
            values = [metric.get(k) for k in ("value", "minimum", "maximum")]
            if not all(type(v) in (int, float) and math.isfinite(v) for v in values):
                errors.append("measurement or acceptance limit is not finite")
            elif not values[1] <= values[0] <= values[2]:
                errors.append(f"acceptance limit failed: {metric.get('name')}")
            if not metric.get("units") or not metric.get("source_file"):
                errors.append("metric lacks units or evidence reference")
            elif metric["source_file"] not in [e.get("path") for e in files]:
                errors.append("metric source is not in the hashed evidence inventory")
        complete = not errors
        prior_complete = prior_complete and complete
        results.append({"stage": stage, "evidence_complete": complete, "errors": errors})
    return {"dossier_complete": all(r["evidence_complete"] for r in results),
            "physical_tests_performed_by_this_audit": False, "deployment_authorized": False,
            "scope": "Integrity/completeness only; reviewer identity and physical truth need human verification",
            "stages": results}
