# S1 graph baseline implementation protocol

Recorded before any graph-baseline training in this checkout (2026-09-04).
The frozen `configs/model2/s1_learned_baseline_eval.json` remains byte-for-byte unchanged.

## Architecture decisions

- Static GNN: seven input features (six normalized observations plus authoritative mask),
  64-wide ReLU encoder, two 64-wide mean-neighbor message layers, 0.1 dropout,
  five-dimensional sigmoid output. Each message layer concatenates self and neighbor
  mean before its linear/ReLU/dropout transform. No self edges in the neighbor mean.
- Temporal GNN: the same spatial encoder followed by a single 64-wide causal GRU
  shared across nodes, then the sigmoid head. Recurrent state resets per scenario.
  Spatial-then-temporal ordering is fixed before training, not selected on test/OOD.
- Graphs align by scenario ID and `tensor_index`. Use undirected topology only;
  no IDs, criticality, node types, lineage, OOD labels, or simulator parameters as features.
- Reuse train-only observed-value normalization/imputation from MLP/GRU.
- Preserve the existing observed-only masked MSE loss for comparability. This does
  not directly supervise unobserved nodes and is a limitation, not a changed objective.
- Select the actual minimum validation MAE checkpoint. Use min_delta only for
  patience, not to discard a better checkpoint. Fail on non-finite/empty loss.
- Preserve all three seeds, AdamW settings, epoch limit, scenario batches and CPU fallback.
- Write selection/checkpoint hashes before final test/OOD; one evaluation per split
  per selected checkpoint. Existing or partial directories cannot be overwritten.
- Finish Static GNN before Temporal GNN. No graph hyperparameter search or OOD tuning.

Alternatives deliberately deferred: graph attention, edge features, interleaved recurrent
message passing, unobserved-target supervision, uncertainty and evidence gates. They
would be new research variants, not these frozen conventional baselines.

## Acceptance

Tests must cover causality, static time independence, node permutation equivariance,
scenario isolation, topology sensitivity, graph ID alignment, authoritative masking,
deterministic initialization, finite output, checkpoint round-trip and overwrite refusal.
Save per-seed config, training logs, selection metadata, checkpoints, all required metrics,
prediction arrays with hashes and failure cases, plus aggregate mean/std.

These are synthetic S1 comparisons only. No proprietary novelty, real weld strength,
physical validation, Model 1 freeze, or deployment approval is established.
