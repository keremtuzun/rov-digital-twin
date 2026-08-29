# Model 2 S1 baseline comparison report

**Result:** `S1 DETERMINISTIC, MLP, AND TEMPORAL GRU COMPARISON COMPLETE`

**S1 release:** `twin2-s1-synthetic-v1`

**Claim boundary:** synthetic internal-comparison evidence only; no proprietary
Model 2, real-world structural-performance, safety, or superiority claim

## Baseline ladder status

| Baseline | Status | Evaluation release | Evidence level |
| --- | --- | --- | --- |
| Last Observation | S1 deterministic evaluation complete | `twin2-s1-synthetic-v1` | Synthetic internal comparison only |
| Simple Heuristic | S1 deterministic evaluation complete | `twin2-s1-synthetic-v1` | Synthetic internal comparison only |
| Independent MLP | S1 learned evaluation complete | `twin2-s1-synthetic-v1` | Synthetic internal comparison only |
| Temporal GRU | S1 learned evaluation complete | `twin2-s1-synthetic-v1` | Synthetic internal comparison only |
| Static GNN | Next implementation gate | Not run | No results |
| Temporal GNN | Deferred | Not run | No results |
| Proprietary Model 2 | Blocked pending baseline matrix | Not run | No results |

Model 1 remains **BLOCKED / NOT FROZEN**.

## Deterministic baseline protocol

Last Observation and Simple Heuristic were rerun on the same strictly validated
S1 release, split IDs, target dimensions, mask semantics, and metric definitions
used by Independent MLP. Both rules predict exclusively from observations and the
authoritative mask. Hidden states are exposed only to metric calculation.

Neither method fits preprocessing, parameters, thresholds, or checkpoints, so no
training or validation-based selection occurs. Validation, test, and OOD are
reported separately. The run creates JSON metrics only and produces no `.pt`,
`.ckpt`, or `.onnx` artifact.

## Independent MLP protocol

The implementation follows the frozen configuration in
`configs/model2/s1_learned_baseline_eval.json`. It treats every node and timestep
independently and consumes the six current observation fields plus the
authoritative observation-mask bit. It uses no temporal history, future evidence,
graph neighbors, or hidden state as input.

Mean imputation and z-score statistics are fitted using observed rows from the S1
train split only. Training uses masked mean squared error, AdamW, scenario batches
of eight, gradient clipping, deterministic algorithms, and the frozen seeds
`2026201`, `2026202`, and `2026203`. Validation MAE alone selects and locks one
checkpoint per seed. Test and OOD are evaluated once only after that lock.

## S1 Independent MLP results

| Seed | Selected epoch | Validation MAE | Test MAE | Test RMSE | OOD MAE | OOD RMSE |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026201 | 6 | 0.117526 | 0.112378 | 0.156137 | 0.216955 | 0.280745 |
| 2026202 | 5 | 0.115077 | 0.109405 | 0.152043 | 0.217821 | 0.283898 |
| 2026203 | 5 | 0.116575 | 0.111161 | 0.154192 | 0.217107 | 0.281956 |
| **Mean** | — | **0.116393** | **0.110981** | **0.154124** | **0.217294** | **0.282199** |

The larger OOD error is descriptive evidence for this frozen synthetic release.
It is consistent with the predeclared OOD shifts and the MLP's inability to use
history or structural neighbors, but this run does not isolate which shift causes
the difference.

### Mean S1 error by observation status

| Split | Mask coverage | Observed MAE | Unobserved MAE |
| --- | ---: | ---: | ---: |
| Validation | 0.517500 | 0.048066 | 0.189676 |
| Test | 0.585000 | 0.046325 | 0.202123 |
| OOD | 0.200833 | 0.093760 | 0.248339 |

The observed/unobserved gap is an expected weak point for an independent,
current-observation model. Temporal GRU tests whether past node-local evidence
helps without introducing graph message passing.

## Temporal GRU protocol and results

Temporal GRU uses the same six normalized observation fields plus mask bit, but
processes each node's sequence causally with a shared one-layer, 64-unit,
unidirectional GRU. It uses no graph, node identity, future observation, or hidden
state input. Train-only preprocessing, masked loss, validation-only checkpoint
selection, and the three frozen seeds match the MLP protocol.

| Seed | Selected epoch | Validation MAE | Test MAE | Test RMSE | OOD MAE | OOD RMSE |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026201 | 68 | 0.097569 | 0.094221 | 0.134030 | 0.198619 | 0.264494 |
| 2026202 | 78 | 0.095703 | 0.092518 | 0.131634 | 0.197496 | 0.262744 |
| 2026203 | 65 | 0.097848 | 0.094935 | 0.134768 | 0.198903 | 0.265231 |
| **Mean** | — | **0.097040** | **0.093891** | **0.133477** | **0.198339** | **0.264156** |

Full implementation, leakage controls, per-state results, artifact inventory,
limitations, and recovery details are in
`docs/MODEL2_S1_TEMPORAL_GRU_REPORT.md`.

## Fair same-release S1 comparison

All values in this table come from `twin2-s1-synthetic-v1`. Learned-baseline
values are three-seed means; each deterministic rule has one fixed,
seed-independent result.

| Baseline | Validation MAE | Validation RMSE | Test MAE | Test RMSE | OOD MAE | OOD RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Last Observation | 0.094959 | 0.149694 | 0.088690 | 0.142571 | 0.274690 | 0.370675 |
| Simple Heuristic | 0.091735 | 0.145614 | 0.085044 | 0.138267 | 0.271088 | 0.367904 |
| Independent MLP, 3-seed mean | 0.116393 | 0.157360 | 0.110981 | 0.154124 | 0.217294 | 0.282199 |
| Temporal GRU, 3-seed mean | 0.097040 | 0.135089 | 0.093891 | 0.133477 | 0.198339 | 0.264156 |

On this one synthetic release, the fixed rules have lower validation and test MAE.
Temporal GRU has lower test RMSE and OOD MAE/RMSE than the other completed
baselines, and lower mean test/OOD error than Independent MLP. This is descriptive,
not a general ranking: the methods use different missing-evidence behavior, and S1
is simulator-generated rather than real inspection data. The table does not prove
Model 2 superiority, real-world performance, calibrated physics, or safety.

## D0 results remain separate

The earlier D0 test scores were:

| Baseline | Release | Test scenarios | Test MAE | Test RMSE |
| --- | --- | ---: | ---: | ---: |
| Last Observation | D0 | 4 | 0.082014 | 0.117144 |
| Simple Heuristic | D0 | 4 | 0.078454 | 0.112116 |

These D0 values remain debug pipeline-smoke evidence and are not combined with,
subtracted from, or ranked against the S1 table. D0 and S1 use different release
contracts, scenario counts, dynamics, and split definitions.

## Reproducible artifacts

Each seed directory under
`reports/model2/s1_learned_baselines/independent_mlp` contains the frozen config
copy, JSONL training log, validation metrics, selected checkpoint and metadata,
test and OOD metrics, prediction arrays and their SHA-256 inventory, prediction
summary, and failure cases. The cross-seed summary is
`reports/model2/s1_learned_baselines/aggregate_summary.json`.

Temporal GRU follows the same per-seed contract under
`reports/model2/s1_learned_baselines/temporal_gru`; its cross-seed aggregate is
stored inside that directory as `aggregate_summary.json`.

The deterministic S1 outputs are isolated at `reports/model2/s1_baselines`:

- `last_observation_s1_metrics.json`
- `simple_heuristic_s1_metrics.json`
- `s1_deterministic_baseline_comparison.json`

| Artifact | SHA-256 |
| --- | --- |
| Aggregate summary | `8576d6193903ec65e1baa4b351c240bf1dbd2b4f7d7a71f1f8adf531fdac5723` |
| Seed 2026201 checkpoint | `959d872dca56159acc76cdf849c8e1e5d996fac9c6934d64d4dccd563df39dc9` |
| Seed 2026202 checkpoint | `167454af9f4e4a0c7e90489b9ac14b2c52d05c18a43bb657b336024bf27d1d0e` |
| Seed 2026203 checkpoint | `cda5f528c8034730bee702c53adc2411fca72bdfd4bb65221bc365496f7faeb7` |
| S1 Last Observation metrics | `aff6242fa249e6e2c31d4e87abda4a4f9693dc9b010391056a91cdc6ba76dc84` |
| S1 Simple Heuristic metrics | `1a3a3657bdb8c369575b011efd0b5511322298c21a71b232648fa4e8c240ee42` |
| S1 deterministic comparison | `41db9bd14872cd0a79220130d3fc5ea051b677f55038193f0892d888d3c8dee7` |
| Temporal GRU aggregate summary | `b3d313011eac360f35342da6efd2b137fcc55c53d554c8a6cd8535555e6586aa` |

Verification includes strict S1 release validation, `138` passing repository
tests, `11` passing subtests, focused deterministic/GRU tests, Ruff, and Python
compilation. The one pytest warning is an existing Starlette/httpx deprecation
warning unrelated to Model 2.

## Next gate

Static GNN is next. It must use the already-frozen S1 configuration and seeds,
preserve train-only preprocessing and validation-only selection, and evaluate
test/OOD only after checkpoint lock. Temporal GNN remains deferred; proprietary
Model 2 remains blocked until the conventional baseline matrix is complete.
