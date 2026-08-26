# Model 2 baseline comparison plan

**Status:** planned; no baseline or Model 2 training performed in this step

## 1. Why baselines come before proprietary claims

A complex graph-temporal system is not a technical contribution merely because it is custom. Simpler methods may explain the same result, and simulator leakage may make an architecture appear stronger than it is. Model 2 R&D can move beyond groundwork only after conventional baselines run on the same immutable data contract, targets, splits, preprocessing, missingness, seeds, and metrics.

The repository currently contains a Failure Twin v0 generator and a historical hand-written heuristic, but no immutable generated dataset snapshot and no completed baseline matrix. Therefore no Model 2 training or superiority claim is authorized now.

## 2. Required baselines

| Baseline | Required inputs | Output target | Training data | Primary metrics | Expected limitation |
| --- | --- | --- | --- | --- | --- |
| **1. Last Observation** | Latest observed feature vector per component, mask, time since observation | Current hidden state; persistence forecast | No learned parameters; train split only for optional normalization | MAE/RMSE, observed versus unobserved error, forecast error | Cannot learn nonlinear dynamics or use topology; stale under long gaps. |
| **2. Independent MLP** | Current component observation, mask, context, node type; no history or neighbors | Current per-component state/discrete severity | Approved Twin 2 train scenarios | MAE/RMSE, macro-F1, calibration | Treats component-times independently; cannot exploit history or graph. |
| **3. Temporal GRU/LSTM** | Per-component observation sequence, masks, time deltas, context | Current and future per-component state | Complete train sequences; validation selects architecture | State/forecast error, missingness robustness, calibration | Uses history but treats structural neighbors independently. |
| **4. Static GNN** | Structure graph and current-time node features/masks | Current per-component state and weak-point ranking | Train scenario graph snapshots only | State error, ranking, weak-point precision/recall | Uses neighbors but has no persistent temporal memory. |
| **5. Temporal GNN** | Graph, node observation sequences, masks, time/context | Current/forecast state, weak-point ranking, uncertainty | Train scenario sequences only | All primary metrics and graph/temporal ablations | Strong generic comparator; may be costly and can overfit simulator dynamics. |
| **6. Simple heuristic risk score** | Latest severity/confidence, time since observation, component criticality; optional fixed neighbor average | Deterministic risk/rank | No fitting except thresholds locked on validation | Ranking, weak-point PR, calibration/reliability | Transparent but thresholds and weights are brittle; not a learned latent-state model. |

The historical `model2_structural_temporal_hypothesis_v0.1` may be adapted as an additional transparent heuristic comparator only if its input semantics are mapped explicitly to Failure Twin v0. It cannot replace any of the six baselines and cannot be called Model 2.

### Common input/output contract

All learned baselines receive only `observations`, `observation_mask`, graph/context fields available at inference, and training-split normalization. `states` are targets/loss inputs in train and evaluation truth in validation/test; they are never model features. At time `t`, a forecast model may consume only evidence with timestamp `<=t`.

The initial target vector is the current five-dimensional synthetic state defined by Failure Twin v0. Results must also report each primitive state separately so aggregate `condition` cannot hide failures. A thresholded weak-point target must be predeclared from synthetic state/criticality before results are inspected.

## 3. Baseline inputs, outputs, and implementation contract

Each implementation must have a versioned config containing feature list, target list, parameter count, optimizer if applicable, learning-rate schedule, batch construction, early-stopping rule, maximum epochs, seed, device, normalization, mask handling, and checkpoint-selection metric.

| Baseline | Missing-observation behavior | Graph behavior | Uncertainty minimum |
| --- | --- | --- | --- |
| Last Observation | Carry last valid observation; record age; population/train mean before any observation | None | Empirical validation residual interval by age bucket |
| Independent MLP | Mask plus train-only imputation; never treat zero as observed | None | Deep ensemble or quantile/variance head after deterministic baseline |
| GRU/LSTM | Mask and time delta enter recurrence; masked inputs use train-only imputation | None | Ensemble/variance head with interval coverage |
| Static GNN | Masked current nodes retained; message passing must not receive hidden truth | Fixed typed/untagged baseline adjacency | Ensemble or calibrated predictive distribution |
| Temporal GNN | Mask-aware temporal encoder and message passing | Fixed graph from the scenario; no test-derived edges | Predictive distribution plus OOD/abstention analysis |
| Heuristic | Explicit unknown/stale penalties | Optional one-hop fixed average as a declared variant | Rule-based uncertainty/unknown band |

## 4. Evaluation metrics

### Primary reconstruction and forecasting

- hidden-state MAE and RMSE, macro-averaged over state dimensions;
- per-state MAE/RMSE for corrosion, crack, material loss, fatigue, and aggregate condition;
- error for all nodes, currently observed nodes, currently unobserved nodes, and never-observed-so-far nodes;
- one-step and configured multi-step forecast MAE/RMSE;
- error by forecast horizon and time since last observation.

### Discrete condition and weak points

- macro/micro F1 and per-class precision/recall if states are discretized;
- weak-point precision, recall, F1, PR-AUC, and false-negative rate at a threshold locked on validation;
- component ranking quality using NDCG@k, precision@k, recall@k, and Spearman rank correlation;
- top-k inspection yield: fraction of true high-state components found within a fixed inspection budget.

### Uncertainty and calibration

- negative log likelihood or proper scoring rule for probabilistic outputs;
- expected calibration error and reliability plots for discretized outputs;
- Brier score where applicable;
- prediction-interval coverage and width for continuous states;
- uncertainty-error correlation, selective risk versus coverage, and abstention performance;
- calibration broken down by observed/unobserved nodes and in-/out-of-distribution scenarios.

### Robustness and ablation

- performance versus observation coverage, contiguous gaps, sensor noise, false-positive/negative rates, sequence length, topology error, and environment level;
- performance with `neighbor_coupling=0` and across coupling strengths;
- modality removal and corrupted-confidence tests;
- graph, temporal memory, mask, time-delta, context, evidence-gate, and uncertainty ablations;
- parameter-count, runtime, peak memory, and inference-latency reporting under the same hardware/software record.

Synthetic scores are simulator-reconstruction results, not physical inspection accuracy or real failure probabilities.

## 5. Comparison protocol

### Gate A — immutable dataset snapshot

1. Generate a versioned Twin 2 snapshot from a reviewed config.
2. Validate schemas, shapes, graph connectivity, masks, timestamps, and truth isolation.
3. Write a complete manifest and SHA-256 inventory.
4. Freeze scenario/asset-group train, validation, and test IDs before model fitting.
5. Record generator commit, environment, config, seeds, and known simulator limitations.

The current deterministic scenario hash split is a debug starting point, not sufficient evidence by itself. The final protocol must prevent the same asset template, initial state, trajectory seed, near-duplicate scenario, or intervention lineage from crossing splits. Test scenarios must include predeclared graph families and parameter/noise/missingness regimes not used for tuning.

### Gate B — fair training

- Use identical split files, observation tensors, masks, target definitions, and evaluation code for every baseline.
- Fit normalization/imputation only on training scenarios.
- Use validation data only for model/threshold selection; open test labels once per frozen comparison release.
- Run at least three predeclared training seeds for learned models and report every run, mean, standard deviation, and confidence interval.
- Fix compute budget or report compute differences transparently.
- Retain best and final checkpoints, logs, configs, dependency lock, and prediction files.
- Never use `states.npy`, future masks/observations, test statistics, scenario config secrets unavailable at inference, or graph construction derived from targets as features.

### Gate C — evaluation and reporting

The evaluator must emit one row per scenario/time/component with target, prediction, uncertainty, mask status, group fields, and model/run ID. Aggregate from this common table. A results release must contain:

| Model/run | Seed | Params | State MAE | Unobserved MAE | Forecast RMSE | Weak-point PR-AUC | NDCG@k | Calibration | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |

Report paired scenario-level differences against the strongest baseline with bootstrap confidence intervals. Do not select only favorable seeds or subgroups.

Failure analysis must include long gaps, low coverage, high noise, topology errors, wrong high-confidence predictions, missed weak points, false priority escalation, graph propagation errors, cold-start components, and regime shifts. Preserve representative scenario IDs and evidence without rewriting failed runs.

### Leakage controls

- Assert disjoint scenario, asset, topology-template, and lineage identifiers across splits.
- Keep hidden state and simulator parameters out of inference payloads.
- Assert each feature timestamp is no later than its prediction cutoff.
- Compute scaling, imputation, class weights, and thresholds from train/validation only.
- Do not tune on test plots, examples, or aggregate metrics.
- Use a negative-control dataset with shuffled graph edges and a zero-coupling dataset.
- Investigate any large graph advantage when `neighbor_coupling=0` as suspected leakage or shortcut learning.
- Hash inputs, configs, splits, checkpoints, and prediction outputs.

## 6. Go / no-go criteria

### Go to proprietary-mechanism implementation

Proceed only when all conditions hold:

- all six baselines are implemented, unit-tested, reproducible, and run on one immutable Twin 2 release;
- dataset/schema/provenance/checksum validation and leakage tests pass;
- primary metrics, weak-point target, thresholds, and uncertainty method were fixed before test evaluation;
- results from at least three learned-model seeds and all negative controls are reported;
- metrics behave meaningfully under coverage, noise, missingness, and coupling interventions;
- the strongest baseline and its failure modes reveal a specific unresolved mechanism that motivates custom Model 2 work;
- no real-world, safety, strength, or novelty claim is inferred from synthetic results.

### Go from synthetic R&D to real-data research

Require a candidate mechanism to improve the predeclared primary metric and unobserved-node metric over the strongest baseline with a paired 95% confidence interval excluding no improvement, while not materially degrading calibration, weak-point recall, or robustness. The exact practical-effect floor must be fixed before the frozen run. This gate authorizes real-data research only—not deployment or proprietary claims.

### No-go / redesign

Stop or narrow the hypothesis if results are not reproducible, leakage cannot be excluded, the temporal GNN or a simpler method matches performance, uncertainty is miscalibrated, gains exist only in one simulator regime, graph gains persist suspiciously under zero coupling, or outputs cannot be tied to evidence. Negative results must remain in the R&D log.

## 7. Current decision

**NO-GO FOR TRAINING IN THIS STEP.** The required immutable Twin 2 dataset release and six-baseline implementation matrix do not yet exist. The next engineering unit is a reviewed dataset-contract validator and baseline implementation specification, followed by generation of a checksummed debug/research snapshot—not Model 2 superiority training.
