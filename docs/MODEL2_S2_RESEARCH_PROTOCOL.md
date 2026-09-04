# Model 2 S2 evidence-memory experiment v0

Frozen before data generation or training on 2026-09-04. User explicitly authorized
continuing the remaining project work in this task. This authorizes local synthetic
R&D, not third-party label approval, legal IP certification or physical deployment.
The machine-readable protocol is `configs/model2/s2_research_protocol.json`.

## Falsifiable hypothesis

Explicit confidence/missingness-gated updates of structural memory may improve
unobserved-node state estimates under partial/noisy evidence relative to conventional
temporal controls. Reject/narrow the claim if controls win or gains disappear in OOD.
This is a custom implementation, not a claim that its component techniques are novel.

At each timestep: encode masked observation; mean-aggregate neighboring previous
memories; predict a latent prior from self/neighbor memory; compute a GRU candidate;
blend prior/candidate using a learned gate multiplied by observed mask and raw
confidence; emit bounded state mean and positive diagonal variance. No observation
means no direct measurement update. A learned prior is NOT a calibrated physical law.
State resets at each independent scenario. No graph attributes, targets, split IDs,
future observations or simulator parameters may enter inference.

## Experiment decisions

- Fresh S2 seeds and IDs, disjoint from S1; 200 scenarios, ten timesteps, ten nodes.
- Preserve S1's documented distributions and lineage separation as the starting design;
  extend the horizon, not make a claim of a new simulator. Combined OOD shift retained.
- Full model; no-memory, no-graph, no-gate and no-uncertainty ablations; conventional
  temporal GRU and temporal GNN controls trained from scratch on exactly S2.
- All models use the same train/validation splits, three fixed seeds and training bounds.
  S2 supervises all hidden synthetic states in the loss, unlike S1's observed-only loss.
  Consequently S1 numbers must NOT be numerically ranked against S2 numbers.
- Variance models optimize Gaussian NLL; deterministic variants/controls optimize MSE.
  The no-uncertainty ablation changes loss too; this is a joint head/objective ablation,
  not an isolated proof that uncertainty improves the mean predictor.
- Validation overall MAE selects actual minimum checkpoints; min_delta controls patience.
- Lock all 21 checkpoints before opening any test/OOD inference. No cross-variant tuning.
- Metrics: overall/state/observed/unobserved MAE/RMSE; Gaussian NLL and raw 90% interval
  coverage/width for uncertainty outputs. ECE for classification is inapplicable to these
  continuous targets. No post-hoc calibration or uncertainty probability claims.
- Report all results including negative findings. Do not promote the model automatically.

## Limitations and next evidence

This release does not isolate individual OOD factors or prove graph-coupling causality.
A subsequent preregistered release must test zero coupling, edge perturbations,
longer sequences, individual noise/coverage shifts, calibration and genuine sensor data.
Weak-point classification and exact strength remain out of scope without targets.
Model 1 and its human review gate are unchanged. No raw actuator commands are emitted.
