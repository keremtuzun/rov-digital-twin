# Model 2 S1 baseline comparison report

**Result:** `INDEPENDENT MLP S1 EVALUATION COMPLETE`

**S1 release:** `twin2-s1-synthetic-v1`

**Claim boundary:** synthetic internal-comparison evidence only; no proprietary
Model 2, real-world structural-performance, safety, or superiority claim

## Baseline ladder status

| Baseline | Status | Evaluation release | Evidence level |
| --- | --- | --- | --- |
| Last Observation | D0 smoke complete | `twin2-d0-debug-v1` | Debug pipeline smoke only |
| Simple Heuristic | D0 smoke complete | `twin2-d0-debug-v1` | Debug pipeline smoke only |
| Independent MLP | S1 learned evaluation complete | `twin2-s1-synthetic-v1` | Synthetic internal comparison only |
| Temporal GRU | Next implementation gate | Not run | No results |
| Static GNN | Deferred until after GRU | Not run | No results |
| Temporal GNN | Deferred | Not run | No results |
| Proprietary Model 2 | Blocked pending baseline matrix | Not run | No results |

Model 1 remains **BLOCKED / NOT FROZEN**.

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
current-observation model. It is one reason the next baseline is Temporal GRU:
that comparison will test whether past node-local evidence helps without yet
introducing graph message passing.

## Relationship to the D0 smoke baselines

The earlier D0 test scores were:

| Baseline | Release | Test scenarios | Test MAE | Test RMSE |
| --- | --- | ---: | ---: | ---: |
| Last Observation | D0 | 4 | 0.082014 | 0.117144 |
| Simple Heuristic | D0 | 4 | 0.078454 | 0.112116 |
| Independent MLP | S1 | 24 | 0.110981 mean over 3 seeds | 0.154124 mean over 3 seeds |

These values are **not a numerical head-to-head comparison**. The deterministic
baselines were run on the small D0 debug release, while the MLP was run on the
larger, lineage-separated S1 release with a distinct generator contract and an OOD
split. Ranking the MLP against the D0 scores would be invalid. Last Observation
and Simple Heuristic must be evaluated on S1 under the same frozen split and
evaluator before any same-release performance comparison is made.

The valid comparison at this stage is procedural: both D0 baselines prove their
non-trained prediction paths, and Independent MLP is the first completed learned
S1 baseline. No method-superiority conclusion follows.

## Reproducible artifacts

Each seed directory under
`reports/model2/s1_learned_baselines/independent_mlp` contains the frozen config
copy, JSONL training log, validation metrics, selected checkpoint and metadata,
test and OOD metrics, prediction arrays and their SHA-256 inventory, prediction
summary, and failure cases. The cross-seed summary is
`reports/model2/s1_learned_baselines/aggregate_summary.json`.

| Artifact | SHA-256 |
| --- | --- |
| Aggregate summary | `8576d6193903ec65e1baa4b351c240bf1dbd2b4f7d7a71f1f8adf531fdac5723` |
| Seed 2026201 checkpoint | `959d872dca56159acc76cdf849c8e1e5d996fac9c6934d64d4dccd563df39dc9` |
| Seed 2026202 checkpoint | `167454af9f4e4a0c7e90489b9ac14b2c52d05c18a43bb657b336024bf27d1d0e` |
| Seed 2026203 checkpoint | `cda5f528c8034730bee702c53adc2411fca72bdfd4bb65221bc365496f7faeb7` |

Verification completed with strict S1 release validation, `126` passing tests,
`11` passing subtests, and focused Ruff checks. The one pytest warning is an
existing Starlette/httpx deprecation warning unrelated to Model 2.

## Next gate

Temporal GRU is next. It must use the already-frozen S1 configuration and seeds,
preserve train-only preprocessing and validation-only selection, and evaluate
test/OOD only after checkpoint lock. Static GNN and Temporal GNN remain deferred;
proprietary Model 2 remains blocked until the conventional baseline matrix is
complete.
