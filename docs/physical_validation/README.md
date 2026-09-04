# Physical validation evidence intake

This task has no identified vehicle/controller/test rig, signed site/risk review, or
real test logs. No thruster, controller or other hardware was energized or commanded.
`dossier.json` is deliberately empty. The audit exits 2, not success.

Run `python scripts/audit_physical_validation.py docs/physical_validation/dossier.json`.
Follow the existing `docs/validation_plan.md` and `docs/hil_architecture.md` with a
qualified operator. This tool does not prescribe new engineering limits or authorize tests.

For each stage, add a record containing:

- `stage`: simulation, recorded_replay, sil, hil, bench, pool, sheltered_water,
  near_shore or open_water, in the established progression.
- `operator`, `independent_reviewer` (different people), `run_id`, `run_timestamp`,
  `vehicle_version`, `software_commit`, `calibration_version`, `risk_review_id`.
- `evidence_origin`: `physical_hardware` for HIL and subsequent stages.
- `critical_safety_events`: actual count; missing or nonzero prevents acceptance.
- `independent_review_decision`: actual review result, not an AI-generated sign-off.
- `evidence_files`: list of `{path, sha256}`; paths are relative to this directory.
- `predeclared_metrics`: list of `{name, value, minimum, maximum, units, source_file}`.
  Limits must be agreed before the test, based on the vehicle/site risk review.

Store private/raw files locally, not in public Git. Provide only reviewed, redacted
evidence intended for repository distribution. The tool checks file integrity and
completeness; it cannot authenticate identities, certify physical truth, or grant
deployment authority. Even a complete dossier reports `deployment_authorized: false`.
