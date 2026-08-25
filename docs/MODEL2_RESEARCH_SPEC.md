# Model 2 research specification

## Formal problem

Model 2 is a dynamic structural-state inference research track. It estimates a component's latent
condition from partial, noisy and sequential Model-1-like evidence:

`P(S_t | O_1, O_2, ..., O_t)`

It is not another image detector, a larger CNN, an LLM, or the existing telemetry health classifier.
Model 1 remains responsible for visible perception. Failure Twin v0 supplies controlled graph dynamics
and numerical observations until an approved Model 1 adapter exists.

## Current implementation boundary

The first research session implements only structural schemas, connected graph generation, hidden state,
configurable degradation, partial/noisy observation generation, scenario-disjoint datasets, debug plots
and automated acceptance tests. No Model 2 network is trained. The existing
`model2_structural_temporal_hypothesis_v0.1` is retained as an earlier transparent heuristic and is not
evidence that the new dynamic-state architecture works.

Hidden fields are corrosion, crack, material loss, fatigue and derived condition. They are written to
`states.npy` strictly for simulator debugging and supervised evaluation. Inference observations retain
every node through a binary mask and expose only noisy defect probabilities, severity estimate,
confidence and context. Debug plots showing hidden state are labeled accordingly.

## Hypothesis and required baselines

The hypothesis is that persistent memory and structural-neighbor context improve hidden-condition
estimation relative to independent observations when observations are missing/noisy and degradation is
coupled. Before Model 2 training, later sessions must implement and compare Last Observation,
Independent MLP, Temporal GRU and Static GNN on identical generated distributions.

The hypothesis should weaken when `neighbor_coupling=0`; a large systematic graph advantage in that
setting is a leakage/debugging signal. Required future ablations are memory, graph, evidence gate and
uncertainty, alone and in specified combinations.

## Metrics and claims

Future evaluation must report hidden-condition MAE for all/observed/unobserved nodes, RMSE,
uncertainty-error correlation and calibration, plus breakdowns by node type, coverage, observation
noise, neighbor coupling and sequence length. Synthetic results are research fixtures, not field
validation or real failure probabilities. Novelty remains unclaimed pending prior-art review.
