# Model 1 Failure Taxonomy

## Evidence status

There is no Model 1 checkpoint, held-out prediction file, or approved image set in the audited repository.
Consequently, the categories below are a review protocol and coverage-gap register—not observed model
failures. Example counts, severity rankings, and a “top failure” list would be fabricated at this stage.

`outputs/model1_audit/failure_index.csv` therefore contains only its schema header. It must be populated from
reviewed held-out predictions, never from the API fixture classifiers.

## Taxonomy

| Code | Failure category | Review rule | Required slice/evidence | Current status |
|---|---|---|---|---|
| F01 | Missed structural damage | Ground truth is crack, corrosion, coating loss, weld defect, deformation, or loose part; predicted normal/other | close and stand-off real inspection frames | Unmeasured |
| F02 | False damage alarm | Benign surface/organism/sediment is predicted as structural damage | biofouling, fish, coral, sediment negatives | Unmeasured |
| F03 | Debris/contamination confusion | Marine debris, oil-like appearance, suspended matter, and structural defect are confused | annotated contamination and clean controls | Unmeasured |
| F04 | Low-visibility collapse | Confidence or correctness fails under turbidity, backscatter, haze, or short visibility | visibility-stratified real frames | Unmeasured |
| F05 | Illumination/color-shift failure | Light falloff, hotspots, blue/green cast, or white-balance changes cause error | illumination and color-temperature strata | Unmeasured |
| F06 | Motion/wave blur | Camera/vehicle motion or waves create blur and false texture | blur magnitude and current/wave metadata | Unmeasured |
| F07 | Scale/viewpoint failure | Small, distant, oblique, or partially occluded anomaly is missed | object-size, distance, and view-angle bins | Unmeasured |
| F08 | Domain shift | Performance changes across ocean, harbor, pool, dry-dock, and synthetic imagery | domain-labelled, mission-disjoint test sets | Unmeasured |
| F09 | Temporal leakage | Adjacent frames from one mission/video enter different splits and inflate metrics | mission/video IDs and duplicate hashes | Blocker |
| F10 | Unknown-class overconfidence | Out-of-scope wildlife, equipment, seabed, or camera artifacts receive high-confidence known labels | explicit unknown/OOD review set | Unmeasured |
| F11 | Label/annotation ambiguity | Reviewers disagree on primary class, defect boundary, or severity | dual-review and adjudication record | Unmeasured |
| F12 | Calibration/abstention failure | Confidence does not reflect correctness or the model fails to abstain | reliability curve, ECE, chosen abstention threshold | Unmeasured |

## Required failure-index fields

Each reviewed false positive, false negative, disagreement, or severe near-miss must record: sample ID,
immutable split, mission/video ID, source and license, ground truth, prediction, confidence, taxonomy code,
visibility, domain, synthetic flag, reviewer, disposition, and a relative image path. Personally identifying or
license-restricted imagery must not be copied into the repository.

## Exit condition

This taxonomy becomes empirical only after the freeze report names a checkpoint and immutable test manifest.
At least all high-severity errors and a representative set from each populated category must be reviewed.
