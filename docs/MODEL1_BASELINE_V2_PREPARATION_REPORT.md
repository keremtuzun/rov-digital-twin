# Model 1 Baseline v2 Preparation Report

**Preparation date:** 2026-08-26  
**Baseline identity:** `model1_baseline_v2`  
**Decision:** **TRAINING-READY CODE / DATA AND ACTIVATION BLOCKED**

## Outcome

The fallback code path is prepared, but no fallback activation, training, evaluation, checkpoint creation, or dataset acquisition occurred. The pipeline fails closed until a complete approved dataset package and a real activation approval exist.

This is the most useful work that can be completed while original checkpoint recovery and dataset permission work remain external blockers. It reduces future execution risk without manufacturing evidence or prematurely training.

## Implemented Controls

- Locked JSON-compatible YAML config at `configs/model1_baseline_v2.yaml`.
- Exact six-domain and nine-condition v2 schemas.
- Separate v2 artifact names that cannot overwrite the missing original checkpoint paths.
- Non-mutating preflight covering:
  - activation approval;
  - required dataset/evidence files;
  - manifest license and reviewer approval;
  - exact `labels.csv`/`split.csv` sample agreement;
  - immutable manifest, labels, and split checksums;
  - mission/video group leakage;
  - real-only primary test data;
  - domain and condition class floors;
  - optional image existence checks.
- Training selection by validation macro F1.
- Weighted cross-entropy without sampler mixing for v2.
- Three-epoch linear warm-up followed by cosine annealing.
- Early stopping with patience 5 and minimum macro-F1 delta 0.002.
- Seeded Python, NumPy, PyTorch, CUDA, sampler, and loader behavior.
- Checkpoint metadata containing v2 identity, task, ordered runtime labels, run ID, config/data/split hashes, and environment.
- Full test prediction output instead of a 20-row preview.
- Evaluation outputs for both classifier heads, calibration, per-class results, source/visibility/domain breakdowns, p50/p95 latency, confusion PNG, and categorized failure-review ledgers.

## Activation Boundary

The repository intentionally does not contain `docs/MODEL1_BASELINE_V2_ACTIVATION_APPROVAL.json`. It may be created only after one of the documented activation reasons is true and an authorized person records the decision:

- `recovery_deadline_passed`;
- `checkpoint_invalid`;
- `evaluation_package_incomplete`.

The approval must retain original Model 1 status as `BLOCKED_NOT_FROZEN`. Its absence is a required blocker, not a missing placeholder to fabricate.

## Current Preflight Evidence

Commands executed without training:

```powershell
python scripts/preflight_model1_baseline_v2.py --config configs/model1_baseline_v2.yaml
python scripts/train_classifier.py --config configs/model1_baseline_v2.yaml --preflight-only
```

Both commands returned exit code `2` with `ready: false`. Reported blockers include the absent dataset root, manifest, labels, immutable split, checksums, license/annotation evidence, validation report, and activation approval.

Checkpoint count before and after the checks: **0 → 0**.

## Verification

- Ruff: passed.
- Unit gate tests: 3 passed.
- Full Python suite: 68 passed, 11 subtests passed, one dependency deprecation warning.
- No `.pt` checkpoint was created.
- No external dataset was downloaded.
- No Model 1 training or evaluation ran.
- No Model 2 or Twin 2 code was changed.

## Files Added or Updated

- `configs/model1_baseline_v2.yaml`
- `src/oceansense/model1_baseline_v2.py`
- `scripts/preflight_model1_baseline_v2.py`
- `scripts/train_classifier.py`
- `scripts/evaluate_multidomain.py`
- `tests/unit/test_model1_baseline_v2_gate.py`
- `docs/MODEL1_BASELINE_V2_FALLBACK_PLAN.md`
- `docs/MODEL1_BASELINE_V2_PREPARATION_REPORT.md`

## Next Action

Continue dataset permission and license-evidence work. On or after a genuine activation decision, create the approval record, assemble the approved immutable dataset package, run preflight, and review its report. Training remains prohibited until preflight returns `ready: true`.
