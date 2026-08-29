# Model 2 D0 baseline smoke report

**Result:** `D0 BASELINE PIPELINE SMOKE PASSED`

**Release:** `twin2-d0-debug-v1`

**Claim boundary:** debug/data-contract evidence only; no training, Model 2 superiority, proprietary, physics, or real-world performance claim

## What and why

Two deterministic, non-trained baselines were run against the strictly validated Twin 2 D0 release:

1. Last Observation
2. Simple Heuristic

The purpose was to test the common release loader, validation-before-load gate, split selection, observation mask, explicit proxy-to-target mapping, hidden-truth isolation, metric aggregation, and JSON report path. This is not proprietary Model 2 implementation or training.

The evaluator uses the frozen 2-scenario validation split and 4-scenario test split separately. It does not fit parameters, inspect the 19 training scenarios, create a checkpoint, or select a threshold. `states.npy` is opened only inside the evaluator as synthetic target truth after predictions have been produced from allowed observations and the mask.

## D0 limitations

D0 contains 25 small, deterministic synthetic scenarios with 4 timesteps and 10 nodes. Its dynamics and noisy observations are uncalibrated debug fixtures. The validation and test samples are far too small for statistical comparison, hyperparameter selection, generalization, structural-safety, field-performance, or IP claims. The D0 manifest explicitly sets `approved_for_model_training=false`.

No weak-point classification metrics were computed because D0 has no predeclared, frozen weak-point target/threshold. Adding a threshold after seeing these results would create an outcome-dependent comparison.

## Baseline definitions

### Last Observation

At every scenario/time/node, the baseline uses the most recent row where `observation_mask=1`. The explicit mapping is:

| Observation proxy | Synthetic evaluation target |
| --- | --- |
| `corrosion_probability` | `corrosion` |
| `crack_probability` | `crack` |
| `material_loss_probability` | `material_loss` |
| `fatigue_probability` | `fatigue` |
| `severity_estimate` | `condition` |

Confidence is not used. Before a node has any observation, all five estimates use the documented `0.0` fallback. The baseline uses no neighbor, graph propagation, future evidence, or hidden state.

### Simple Heuristic

For an observed node, each primitive estimate is:

`confidence * defect_probability + (1 - confidence) * severity_estimate`

The aggregate condition estimate is:

`confidence * severity_estimate + (1 - confidence) * mean(defect_probabilities)`

The resulting five-dimensional vector is clipped to `[0,1]` and carried forward per node. The pre-observation fallback is `0.0`. The rule is deterministic and neighbor-agnostic and has no learned parameters.

## Metrics and results

MAE and RMSE aggregate all scenario/time/node/state entries in the named split. Observed/unobserved values are grouped by the current timestep’s mask, even if an unobserved node has earlier carried evidence. Count fields in JSON refer to timestep/node entries; errors average their five state dimensions.

| Baseline | Split | Scenarios | Coverage | Overall MAE | Overall RMSE | Observed MAE | Unobserved MAE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Last Observation | Validation | 2 | 0.425 | 0.081511 | 0.118566 | 0.066199 | 0.092829 |
| Last Observation | Test | 4 | 0.475 | 0.082014 | 0.117144 | 0.073617 | 0.089612 |
| Simple Heuristic | Validation | 2 | 0.425 | 0.078484 | 0.115401 | 0.061836 | 0.090789 |
| Simple Heuristic | Test | 4 | 0.475 | 0.078454 | 0.112116 | 0.068516 | 0.087445 |

Per-state-dimension MAE/RMSE and exact unrounded values are preserved in the metric JSON files. Simple Heuristic has lower aggregate error than Last Observation on this one D0 snapshot. That is a descriptive smoke result only—not evidence of superiority—because D0 is tiny, synthetic, single-seed, uncalibrated, and not approved for model selection.

## Output evidence

| Output | SHA-256 |
| --- | --- |
| `last_observation_metrics.json` | `9d031e2130a37c2c7e57255f06a02b1f1ecc27267886fe7c08df2c2f570ebc6e` |
| `simple_heuristic_metrics.json` | `8a719c54cff1d3589d7eca151695adf88ab1e9b1294d3ee9b8ab879141de9a1b` |
| `baseline_comparison.json` | `628bd041c55874957aebcda4d5286535476e2301353c85fa86ffe9596435e4a1` |

All files reference D0 manifest SHA-256 `95f9fdb4d801eace1add7cee37fb14f0563dc7d41c93d48edd0d46c20324b62a` and state `training_performed=false`, `debug_only=true`, and that no Model 2 superiority claim is supported.

## Leakage controls

- `load_d0_release` invokes strict D0 validation before loading arrays.
- Baseline function signatures accept exactly `observations` and `mask`; they cannot receive hidden states.
- Predictions are generated for one split from that split’s observation/mask slice before target error is computed.
- Only evidence at or before the current timestep is carried forward; future observations are never read.
- The mask—not a zero observation—is authoritative.
- The inference-input list excludes `states.npy` and includes only observations, mask, and structure graph.
- Both smoke baselines are neighbor-agnostic and do not use graph-derived target shortcuts.
- Validation and test metrics are emitted separately; no combined score hides split behavior.
- No training, optimizer, learned weights, checkpoint, ONNX file, or threshold selection occurs.

## What this proves

- the immutable D0 release can be validated and loaded by a common evaluator;
- split IDs correctly select 2 validation and 4 test scenarios;
- two deterministic prediction paths handle masked and carried observations;
- hidden synthetic targets can be isolated to metric calculation;
- required aggregate, per-state, and observed/unobserved metrics serialize reproducibly apart from the recorded run timestamp;
- the output contract and claim-boundary fields work end to end.

## What this does not prove

- that Model 2 has been implemented or trained;
- that one baseline is generally better than another;
- that any method detects real degradation or predicts hidden structural condition at sea;
- that D0 dynamics represent corrosion, cracks, material loss, fatigue, strength, or failure physics;
- that the method is novel, proprietary, calibrated, safe, deployable, or competition-ready;
- that Model 1 outputs are integrated or validated;
- that Unity/Twin 1 navigation validates any result here.

Model 1 remains **BLOCKED / NOT FROZEN**.

## Reproduction

```powershell
python scripts/validate_model2_release.py `
  --release-dir data/model2/d0_debug `
  --strict `
  --require-debug-d0

python scripts/run_model2_d0_baselines.py `
  --release-dir data/model2/d0_debug `
  --output-dir reports/model2/d0_baselines
```

The second command rewrites report timestamps and therefore report-file hashes. Core predictions and metrics remain deterministic for the same release and code.

## Next baseline gate

Do not train learned models on D0. The separately versioned S1 synthetic release
and frozen learned-baseline contract have since been created, and Independent MLP
and both deterministic baselines have since completed S1 evaluation. Independent
MLP has also completed its first S1 evaluation. See
`docs/MODEL2_S1_BASELINE_COMPARISON_REPORT.md` for its synthetic-only results and
the fair same-release S1 table. These D0 scores remain separate debug evidence.
Temporal GRU is the next implementation gate. Static GNN, Temporal GNN, and any
proprietary Model 2 mechanism remain deferred.
