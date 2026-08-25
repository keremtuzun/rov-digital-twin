# Model 1 Failure Taxonomy

## Summary

No visual checkpoint, held-out predictions, or approved image set exists. The categories below are a review
protocol and coverage-gap register, not observed or ranked Model 1 failures. Counts and “top errors” would be
fabricated. `outputs/model1_audit/failure_index.csv` contains only its schema header.

## Failure Categories

| Required category | Review rule / evidence slice | Current status |
|---|---|---|
| Blur | motion/wave blur magnitude and clean counterpart | Unmeasured |
| Low light | illumination strata, hotspots and color shift | Unmeasured |
| Turbidity | visibility/backscatter strata from real missions | Unmeasured |
| Marine growth | biofouling positives and benign organism negatives | Unmeasured |
| Occlusion | partial component/defect coverage with occlusion metadata | Unmeasured |
| Small cracks | scale-verified close/stand-off crack imagery | Unmeasured |
| Corrosion texture ambiguity | corrosion vs stain, sediment, growth and intact coating | Unmeasured |
| Weld/bolt/component confusion | explicit weld, bolt, fastener, joint and pipe labels | Unmeasured |
| Viewpoint/distance | object-size, distance and oblique-view bins | Unmeasured |
| Class imbalance | per-class counts and macro/per-class metrics | Blocked: no manifest |
| Annotation uncertainty | dual review, agreement and adjudication | Unmeasured |
| Out-of-domain imagery | wildlife, seabed, equipment, dry-dock and synthetic OOD sets | Unmeasured |
| Sensor/modality limitation | RGB-only failure cases; sonar/sensor evidence kept separate | Unmeasured |

Additional index codes should cover temporal split leakage, unknown-class overconfidence and
calibration/abstention failure.

## Representative Examples

Example path/index: `outputs/model1_audit/failure_index.csv`. It contains no rows because examples cannot be
selected without a checkpoint, immutable test split and reviewed predictions. Required fields include
sample/split/mission/source/license, truth, prediction, confidence, category, visibility, domain, synthetic
flag, reviewer, disposition and relative image path.

## Recommended Targeted Fixes

No model fix is supported yet. The evidence-backed actions are measurement prerequisites: license-approved
data, mission-disjoint splits, checkpoint provenance, held-out predictions and dual-reviewed failure indexing.
Reprioritize fixes only after those artifacts exist.
