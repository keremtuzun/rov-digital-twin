# Model 1 v1 freeze report

## Freeze decision

**Blocked - no Model 1 v1 artifact has been frozen.**

The repository contains conventional image classification/detection training and evaluation code, but it
does not contain all required freeze inputs:

- no license-reviewed, immutable real underwater inspection dataset snapshot;
- no approved Model 1 checkpoint tied to that snapshot;
- no final validation/test prediction file;
- no reproducible metrics, failure gallery or per-class failure analysis for such a checkpoint.

The committed telemetry weak-point classifier and Unity PPO checkpoint are different system components.
Neither is a substitute for the conventional visual-inspection Model 1.

## What can be reproduced now

- Dataset governance, license audit and mission/video-disjoint splitting.
- Conventional image training entry points once approved inputs exist.
- Shared prediction validation and evaluation through `scripts/evaluate_predictions.py`.
- Failure-index export when prediction metadata includes ground-truth labels and reviewed failure causes.

## Freeze gate

Model 1 v1 may be frozen only after a reviewed run provides checkpoint hash, git commit, environment,
training config, label schema, dataset manifest, precision/recall/F1, per-class false positives and false
negatives, latency/throughput, robustness subsets and a representative failure index. Retraining after
freeze must use a new experiment/version name; the v1 package must remain immutable.
