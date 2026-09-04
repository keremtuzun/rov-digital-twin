# S2 custom Model 2 research results - 2026-09-04

**Implemented and evaluated: synthetic research only, not approved for deployment.**

The user's follow-up authorized proceeding with the separate research/data track.
The preregistered protocol and authorization scope are in
`configs/model2/s2_research_protocol.json` and `MODEL2_S2_RESEARCH_PROTOCOL.md`.
Neither S1's immutable release nor its proprietary-training prohibition was changed.

## What ran

- Fresh `twin2-s2-research-v1`: 200 scenarios, ten timesteps, ten nodes; split counts
  120 train / 32 validation / 24 test / 24 OOD, separated by lineage.
- Generation seeds 20269001-20269004 and training seeds 2026901-2026903.
- Five evidence-memory variants plus independently trained GRU and Temporal GNN controls:
  21 runs total. No pretrained S1 checkpoints or S1 test/OOD targets were used.
- All 21 validation-selected checkpoints were locked before test/OOD model inference.
- CPU deterministic training, 32-wide hidden state, maximum 60 epochs, patience 8,
  train-only preprocessing, all-state synthetic supervision, no hyperparameter search.
- Saved means, variances where applicable, metrics, logs, checkpoints, protocol,
  matrix lock and per-run completion hashes. The auditor recomputes metrics from
  saved predictions without rerunning model inference.

## Three-seed means

| Variant | Validation MAE | Test MAE | OOD MAE | Test unobserved MAE | OOD unobserved MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full evidence memory | 0.062061 | 0.061081 | 0.224036 | 0.081283 | 0.259920 |
| No memory | 0.130960 | 0.141727 | 0.386957 | 0.255243 | 0.463029 |
| No graph | 0.068224 | 0.067147 | 0.261723 | 0.093541 | 0.308955 |
| No evidence gate | 0.062143 | 0.061789 | 0.253802 | 0.082055 | 0.297573 |
| No uncertainty head / MSE loss | 0.057028 | 0.056932 | 0.209851 | 0.074373 | 0.245238 |
| Conventional Temporal GRU | 0.069515 | 0.068825 | 0.256734 | 0.088972 | 0.299003 |
| Conventional Temporal GNN | 0.055588 | 0.059370 | 0.232335 | 0.072653 | 0.271234 |

Full metrics, population standard deviations, state-dimension breakdowns and raw
coverage are in `reports/model2/s2_research_v0/summary.json` and per-seed directories.

## Interpretation and negative findings

The full custom model has lower test/OOD error than the GRU control here, but the
conventional Temporal GNN has lower validation/test error and lower test unobserved-node
error. The no-uncertainty variant has lower overall test/OOD error than the full model.
These results do NOT establish general custom-model superiority.

Memory removal strongly hurts this task; graph/gate removal also worsens some metrics.
The no-memory ablation zeros persistent neighbor memory too, so it is not an isolated
test of spatial information. The no-uncertainty ablation also changes NLL to MSE, so
head and objective effects are confounded. Parameter counts/optimization behavior differ.

The full model's raw nominal 90% intervals cover **88.91%** of test targets but only
**60.34%** of OOD targets. That is serious OOD undercoverage. The intervals are NOT
reliably calibrated under shift and must not drive structural-safety decisions.
No calibration fit or post-test tuning was performed. No production model was selected.

S2 has different supervision, horizon and seeds from S1; do not rank their numbers
directly. This is one small synthetic simulator family with a combined OOD shift, not
proof of weld strength, microcrack detection, multimodal sensing, physical truth or novel IP.

## Reproduction and evidence

```bash
export PYTHONPATH=src
python -m pytest -q
python scripts/audit_model2_s2_research.py
```

Training entrypoint: `python scripts/run_model2_s2_research.py`. It refuses an existing
experiment directory to prevent overwriting evidence or repeating held-out evaluation.
Do not delete reports merely to run the command again. Use a new preregistered protocol
and new holdouts for further experiments. Source hashes and versions are recorded in
`environment.json`; production inference integration is deliberately absent.

## Next research gate

Do not promote v0. A new preregistered experiment should isolate individual OOD shifts,
zero-coupling/topology perturbations and longer horizons, define a train/validation-only
calibration procedure, and evaluate once on fresh holdouts. Obtain real sensor and
engineering labels before any physical capability claim. No external disclosure or
GitHub push was performed for this custom research implementation.
