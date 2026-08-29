# Model 2 S1 Temporal GRU report

**Result:** `TEMPORAL GRU S1 EVALUATION COMPLETE`

**Release:** `twin2-s1-synthetic-v1`

**Claim boundary:** synthetic internal-comparison evidence only; no real-world
structural-performance, safety, proprietary Model 2, or superiority claim

## What was implemented

The Temporal GRU is a shared, node-local recurrent baseline. For each structural
node it processes the five S1 timesteps in chronological order and emits a
five-dimensional hidden-state estimate at every timestep. It has 14,341 trainable
parameters and follows the frozen architecture exactly:

- input dimension 7: six observation fields plus the authoritative mask bit;
- hidden dimension 64;
- one unidirectional GRU layer;
- zero recurrent dropout;
- sigmoid output head for the five bounded state dimensions;
- no graph message passing, node-identity embedding, or proprietary mechanism.

Independent MLP treats every node-timestep independently. Temporal GRU differs
only by retaining a node-local recurrent state over current and past evidence. It
therefore tests temporal memory without introducing structural neighbors.

## Input and preprocessing contract

Only `observations.npy` and `observation_mask.npy` supply model features.
`structure_graph.json` remains part of release validation but is not consumed by
the model. `states.npy` is used only as the supervised target and evaluation
truth.

Mean imputation and z-score statistics are fitted once from observed rows in the
S1 train split. Masked observation vectors become zero after normalization,
equivalent to train-observed-mean imputation, and the mask bit explicitly
distinguishes them from real mean-valued evidence. Validation, test, and OOD
values never contribute to preprocessing.

## Temporal leakage prevention

The GRU is unidirectional. Inputs are reshaped from
`[scenario,time,node,feature]` to independent `[scenario*node,time,feature]`
sequences without changing time order. The output at timestep `t` can depend only
on observations at timesteps `<=t`. A focused test changes all future inputs and
requires earlier outputs to remain bit-identical. The model accepts one `inputs`
argument and cannot receive hidden state targets or graph neighbors.

## Training and checkpoint selection

The run uses the frozen settings: AdamW, learning rate `0.001`, weight decay
`0.0001`, up to 100 epochs, scenario batch size 8, masked mean squared error,
gradient clipping at 1.0, early-stopping patience 12, minimum delta `0.0001`, no
mixed precision, zero data-loader workers, and deterministic Python/NumPy/Torch
seeding.

All fitting uses the train split. Validation overall MAE selects the exact lowest
validation checkpoint independently for seeds `2026201`, `2026202`, and
`2026203`. The selected checkpoint and its SHA-256 metadata are written before
test or OOD access. Test and OOD are then each evaluated once per selected
checkpoint.

## Per-seed results

| Seed | Selected epoch | Validation MAE/RMSE | Test MAE/RMSE | OOD MAE/RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 2026201 | 68 | 0.097569 / 0.135578 | 0.094221 / 0.134030 | 0.198619 / 0.264494 |
| 2026202 | 78 | 0.095703 / 0.133465 | 0.092518 / 0.131634 | 0.197496 / 0.262744 |
| 2026203 | 65 | 0.097848 / 0.136223 | 0.094935 / 0.134768 | 0.198903 / 0.265231 |

## Aggregate results

| Split | Mean MAE | MAE population std. | Mean RMSE | RMSE population std. | Mask coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Validation | 0.097040 | 0.000952 | 0.135089 | 0.001178 | 0.517500 |
| Test | 0.093891 | 0.001014 | 0.133477 | 0.001338 | 0.585000 |
| OOD | 0.198339 | 0.000608 | 0.264156 | 0.001043 | 0.200833 |

### Mean error by observation status

| Split | Observed MAE/RMSE | Unobserved MAE/RMSE |
| --- | ---: | ---: |
| Validation | 0.038891 / 0.051853 | 0.159407 / 0.186916 |
| Test | 0.038390 / 0.051806 | 0.172128 / 0.197856 |
| OOD | 0.076543 / 0.098538 | 0.228947 / 0.291330 |

### Mean per-state MAE

| Split | Corrosion | Crack | Material loss | Fatigue | Condition |
| --- | ---: | ---: | ---: | ---: | ---: |
| Validation | 0.099057 | 0.097685 | 0.097282 | 0.097645 | 0.093529 |
| Test | 0.095831 | 0.096943 | 0.095373 | 0.090621 | 0.090689 |
| OOD | 0.202055 | 0.201707 | 0.195937 | 0.197406 | 0.194591 |

Exact per-state MAE/RMSE distributions are preserved in the aggregate JSON.

## Same-release S1 comparison

| Baseline | Validation MAE/RMSE | Test MAE/RMSE | OOD MAE/RMSE |
| --- | ---: | ---: | ---: |
| Last Observation | 0.094959 / 0.149694 | 0.088690 / 0.142571 | 0.274690 / 0.370675 |
| Simple Heuristic | 0.091735 / 0.145614 | 0.085044 / 0.138267 | 0.271088 / 0.367904 |
| Independent MLP, 3-seed mean | 0.116393 / 0.157360 | 0.110981 / 0.154124 | 0.217294 / 0.282199 |
| Temporal GRU, 3-seed mean | 0.097040 / 0.135089 | 0.093891 / 0.133477 | 0.198339 / 0.264156 |

On this synthetic release, Temporal GRU has lower mean test and OOD error than
Independent MLP. Its mean test MAE remains higher than the two fixed rules, while
its test RMSE and OOD MAE/RMSE are lower. These are descriptive S1 results, not a
general superiority conclusion. S1 cannot establish performance on real ROV
inspection data, calibrated structural physics, operational safety, or a
proprietary Model 2 contribution.

## Artifacts and recovery record

Every seed directory under
`reports/model2/s1_learned_baselines/temporal_gru` contains the frozen config
copy, JSONL training log, checkpoint, selected-checkpoint metadata, validation,
test and OOD metrics, prediction arrays and hashes, prediction summary, and
failure cases. The cross-seed summary is `aggregate_summary.json`, SHA-256
`b3d313011eac360f35342da6efd2b137fcc55c53d554c8a6cd8535555e6586aa`.

The first seed-2026203 attempt encountered a checkpoint rewrite error before
selection or final evaluation. Its three partial files were removed. Atomic
checkpoint replacement and completed-seed audit/resume logic were added; completed
seeds 2026201 and 2026202 were reused without repeating test/OOD, and only seed
2026203 was rerun. Final artifact hashes and prediction shapes pass audit.

## Limitations

- S1 is synthetic simulator data and has no real-world validation.
- Training loss is masked to currently observed nodes; missing-node inference is
  learned indirectly through recurrent state and population behavior.
- The five-timestep sequences provide only a short temporal-memory test.
- The GRU has no structural neighbors, graph topology, node identity, uncertainty
  head, or weak-point target.
- OOD contains several simultaneous shifts, so this run cannot attribute the OOD
  difference to one cause.
- Model 1 remains **BLOCKED / NOT FROZEN**.

## Verification

Strict S1 validation passed before training. Focused GRU tests cover output and
sequence shapes, mask/imputation behavior, causal no-future behavior,
deterministic initialization, atomic checkpoint writing, validation-only
selection metadata, metric schema, and artifact location. The full repository
suite passed with 138 tests and 11 subtests. Ruff and Python compilation passed.
All required files, checkpoint/config hashes, and prediction shapes/hashes passed
the post-run audit.

## Next baseline recommendation

Static GNN is the next frozen conventional baseline. It should test current-time
structural message passing without temporal memory, using the same seeds,
train-only preprocessing, validation-only checkpoint selection, and locked final
test/OOD protocol. Temporal GNN and proprietary Model 2 remain deferred.
