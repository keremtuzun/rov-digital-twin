# Model 2 research log

## 2026-09-04: conventional baseline matrix completed locally

Continued from remote Temporal GRU commit `69d7f2e`, which was newer than the supplied
project history. Implemented Static GNN then Temporal GNN under the unchanged S1 config,
all three fixed seeds, with pre-training decisions recorded in
`MODEL2_S1_GRAPH_BASELINE_PROTOCOL.md`. All six conventional comparators now have results.
Temporal GNN improves in-distribution unobserved-node error, but GRU remains better on OOD.
No proprietary Model 2 was trained and no Model 1 approval was fabricated.

Repaired a real cross-platform release failure: Git newline normalization changed
hashed JSON bytes. Restored only hash-proven originals, retained original checksums,
disabled Git conversion for immutable evidence, and made v1 release writers explicit
about CRLF. Cross-platform reproducibility distinguishes data from truthful runtime
provenance. Hardened missing-supervision and GRU recovery checks; fixed CI test dependencies.

Current evidence and next gates: `CONRAD_DEVELOPMENT_STATUS_2026_09_04.md`.
Older entries below are historical and should not be read as current baseline status.

## Track correction from the standalone specification

Model 2 is now formally a dynamic structural-state inference track. It estimates hidden, evolving
component condition from partial/noisy observation sequences. It is not a second detector, a bigger
vision model or a generic LLM task. The new `oceansense.model2` Failure Twin v0 provides the graph,
hidden dynamics, observation masks and scenario-level debug dataset required before baseline or Model 2
training.

The earlier heuristic below remains a transparent pre-v0 idea only. Its existence does not satisfy the
new baseline matrix and its historical synthetic outputs are not evidence for the dynamic-state
hypothesis.

## Earlier capability gap

Conventional single-frame inspection models label visible pixels or frames but do not establish whether
evidence persists across time/viewpoints or whether observations agree with the inspected structure's
relationships. A confident single view can therefore be brittle, poorly localized in structural context
or misleading under turbidity and occlusion.

## Primary hypothesis

A transparent structural-temporal evidence mechanism can improve concern ranking and reinspection
decisions by combining:

- Model 1 concern scores and uncertainty;
- viewpoint angle and distance weighting;
- persistence across distinct frames;
- relations such as weld-connects-pipe and coating-on-component;
- an explicit unknown state when history or viewpoint diversity is insufficient.

The implemented prototype is `model2_structural_temporal_hypothesis_v0.1`. It produces a structured
condition state and mechanism trace. It is evaluated against three required ablations: without temporal
memory, without structural support and Model 1 score-only.

## Fallback hypothesis

If structural metadata is too unreliable, temporal persistence plus viewpoint-aware uncertainty alone
may improve reinspection decisions over a single-frame threshold.

## What is not yet proven

- No literature matrix or novelty review has been completed in this repository.
- No real Model 1 checkpoint or approved field dataset has evaluated the hypothesis.
- Thresholds are engineering hypotheses, not calibrated structural-risk probabilities.
- The code is not called a proprietary invention until novelty and empirical contribution are supported.
- Last Observation and Simple Heuristic have D0 debug-smoke results and no-training S1 results.
  Independent MLP and Temporal GRU have completed the frozen S1 synthetic evaluation, but Static GNN
  and Temporal GNN have not been run. D0 and S1 scores remain separate, and proprietary Model 2
  training remains blocked by design until the conventional baseline matrix is complete.

## Falsifiable experiment

Run the full mechanism and all ablations on the same mission-grouped records. Compare false acceptance,
reinspection recall, temporal consistency, calibration and synthetic-to-real behavior separately. Reject
the primary hypothesis if it does not consistently outperform score-only and temporal-only baselines on
held-out real missions.
