# Model 2 S1 Learned-Baseline Evaluation Configuration

## Freeze status

The S1 learned-baseline evaluation configuration is **frozen before any learned
baseline is run**. The machine-readable source of truth is
`configs/model2/s1_learned_baseline_eval.json`, with config SHA-256
`59f8a1dd3a24ef67c48d35b985eea65d13a1ce97dbf4273a98eebf5d8e3670b2`.

Freezing first prevents later choices from being influenced by validation, test,
or OOD results. It fixes the compared methods, random seeds, inputs, split roles,
selection metric, resource bounds, outputs, and claim boundary before learned
results exist. No training or learned-baseline execution was performed as part of
this freeze.

## Bound S1 release

The configuration records and requires the immutable synthetic release:

- Path: `data/model2/s1_synthetic`
- Release ID: `twin2-s1-synthetic-v1`
- Manifest SHA-256:
  `2adba7821141d673e12487cf1e8f4767fb777de828630b4b98019d5e302cec33`
- Validation mode: strict S1 validation with `require_synthetic_s1`

The config loader can validate the release and reject a manifest checksum mismatch
before a baseline runner is permitted to use it.

## Included conventional baselines

Only these four conventional comparison baselines are in scope:

1. `independent_mlp`
2. `temporal_gru`
3. `static_gnn`
4. `temporal_gnn`

No proprietary Model 2 method is included. The validator rejects missing,
additional, renamed, or proprietary baseline entries.

## Seed and deterministic execution rules

Every baseline must use all three frozen training seeds:

- `2026201`
- `2026202`
- `2026203`

At least three unique positive integer seeds are mandatory. Python, NumPy, and
PyTorch must be seeded, deterministic algorithms are required, and data-loader
workers are fixed at zero. CUDA may be used when available, but a CPU fallback is
required. These rules reduce avoidable run-to-run variation; they do not imply that
identical results are guaranteed across all hardware and library versions.

## Split and feature rules

Split use is frozen as follows:

| Split | Permitted use |
| --- | --- |
| Train | Training only; fit normalization and imputation here only |
| Validation | Hyperparameter and checkpoint selection only |
| Test | One final in-distribution evaluation after checkpoint lock |
| OOD | One final out-of-distribution evaluation after checkpoint lock |

Splits must remain scenario-level, lineage-disjoint, and independent of target
values. Inputs are limited to `observations.npy`, `observation_mask.npy`, and
`structure_graph.json`. `states.npy` is a target for loss and evaluation only; it
must never be supplied as an input. The mask is authoritative, and future
observations or other future evidence are forbidden.

## Checkpoint selection

Each baseline and seed selects its best checkpoint by minimizing
`validation.mae_overall`. Test and OOD data cannot influence hyperparameters,
early stopping, checkpoint selection, threshold selection, preprocessing, or
reruns. After the checkpoint is locked, test and OOD are each evaluated exactly
once. Every saved checkpoint and config copy must have a SHA-256 recorded.

## Required metrics

Every completed baseline evaluation must report:

- overall MAE and RMSE
- per-state-dimension MAE and RMSE
- observed-node error
- unobserved-node error
- mask coverage

Weak-point metrics are disabled because S1 v1 has no predeclared frozen weak-point
target. If a model emits uncertainty, negative log likelihood, expected calibration
error, and prediction interval coverage are additionally required.

## Artifact contract

All outputs are confined to `reports/model2/s1_learned_baselines`. Each
`{baseline}/seed_{seed}` directory must contain the frozen config copy, training
log, validation metrics, selected checkpoint and its metadata, test metrics, OOD
metrics, prediction summary, and failure cases. The cross-run aggregate is fixed at
`reports/model2/s1_learned_baselines/aggregate_summary.json`. Relative traversal
and absolute output paths are rejected.

## Leakage and claim boundaries

The following are enforced as fail-closed rules: hidden states cannot be inputs;
lineages cannot cross splits; targets cannot determine split assignment;
normalization and imputation fit train only; future evidence is forbidden; and
neither test nor OOD may be used for tuning or model selection.

S1 is synthetic and may provide only internal comparison evidence. It cannot prove
real-world structural performance or proprietary-model superiority. Model 1
remains **BLOCKED / NOT FROZEN**. This config neither changes that status nor
creates Model 1 checkpoints or labels.

## Next gate

After this configuration, validator, tests, and documentation are committed, the
next permitted step is to implement and run **Independent MLP only** under this
frozen contract. GRU, static GNN, temporal GNN, and any proprietary Model 2 work
remain outside this gate.
