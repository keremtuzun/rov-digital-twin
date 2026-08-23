# OceanSense gap analysis

Audit date: 2026-08-23. Baseline commit: `90dd5db`.

## Canonical telemetry mismatch

- Problem: Unity emitted seven fields while `TelemetrySample` required eighteen canonical fields.
- Evidence: previous `TelemetryUdpBridge.BuildTelemetryJson` and `src/rov_dt/schema.py` differed in names and cardinality.
- Affected files: Unity telemetry/power sensor, `config/telemetry_schema_v1.json`, Python adapter, ROS nodes.
- Risk: ROS diagnostic rejection or node exception; misleading default values.
- Proposed solution: versioned contract, simulated/derived provenance, validation before ROS publication.
- Verification: `tests/test_telemetry_contract.py` and static Unity schema-field check.
- Status: implemented; live Unity/ROS verification blocked by unavailable runtimes.

## ROS invalid-input handling

- Problem: invalid JSON or missing fields propagated exceptions from the subscription callback.
- Evidence: prior callback directly called `json.loads` and `TelemetrySample.from_dict`.
- Affected files: `diagnostic_node.py`, `unity_udp_bridge.py`.
- Risk: diagnostic service interruption.
- Proposed solution: catch a typed contract error, warn and return without publishing.
- Verification: malformed/missing-field unit tests; ROS live test in acceptance plan.
- Status: implemented; ROS runtime verification required.

## Unity Editor acceptance

- Problem: code-authoring host has no Unity Editor, so C# compilation, generated assets and Play Mode have not run.
- Evidence: Unity executable and Hub Editor directory were absent during the repository audit.
- Affected files: all Unity runtime/editor code.
- Risk: editor/API-version or scene wiring defect can remain despite static checks.
- Proposed solution: deterministic batch commands and acceptance checklist.
- Verification: `docs/unity_acceptance_test.md`.
- Status: blocked — editor verification required; installation was not attempted.

## Dataset licensing and provenance

- Problem: no approved real snapshot exists; source-level openness was previously easy to confuse with asset licensing.
- Evidence: `models/` contains only `.gitkeep`; dataset contains schema examples and zero approved assets.
- Affected files: `dataset/sources.yaml`, license register, manifests and governance scripts.
- Risk: unlicensed training, non-reproducible results, invalid claims.
- Proposed solution: Public Domain/CC0/CC BY 4.0 allowlist plus explicit reviewer, checksum and attribution gates.
- Verification: governance unit tests and empty approved manifest by default.
- Status: implemented infrastructure; acquisition requires user approval and asset review.

## Label duplication and diagnostic overclaim

- Problem: crack/corrosion/visibility/fish/coral aliases fragmented small datasets and implied diagnoses.
- Evidence: legacy `CONDITION_LABELS` contains overlapping names.
- Affected files: taxonomy, label config, converters, schemas.
- Risk: unstable metrics and unsafe semantic claims.
- Proposed solution: nine cautious canonical labels while retaining old API aliases.
- Verification: taxonomy/conversion/backward-compatibility tests.
- Status: implemented.

## Split leakage and evaluation coverage

- Problem: prior image and telemetry split logic randomized individual records; adjacent frames/rows could cross splits.
- Evidence: prior `stratified_split` and `_stratified_split` operated per record within label buckets.
- Affected files: image data module, telemetry training, training/evaluation scripts.
- Risk: inflated held-out performance.
- Proposed solution: mission/video group split, duplicate audit, macro F1, balanced accuracy, ECE, thresholds and safety false negatives.
- Verification: group-disjoint tests and dependency-light metric tests.
- Status: implemented core; full image evaluation blocked on approved data.

## Synthetic, SIL, HIL and field evidence

- Problem: domain-randomized image capture, fault scenarios and gated field criteria were incomplete.
- Evidence: no capture metadata sidecar or formal staged acceptance document existed.
- Affected files: Unity synthetic/fault components and validation plans.
- Risk: synthetic/real contamination or premature field deployment.
- Proposed solution: sidecar metadata, explicit fault controller, separate real/synthetic reports and staged HIL plan.
- Verification: Unity Play Mode, ROS bag replay and operator sign-off stages.
- Status: implemented design; physical stages blocked on hardware, approved operators and test site.
