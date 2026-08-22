# Model card: OceanSense perception v1

Two ImageNet-pretrained EfficientNet-B0 classifiers are supported: one for inspection domain and one for
visible condition. The condition response includes top-k probabilities. The optional detector is YOLOv8n
and must only be trained when genuine bounding-box annotations exist.

Training and evaluation code reports test accuracy, per-class precision/recall/F1, a confusion matrix,
and 20 JSON-compatible sample predictions for either task. No trained image checkpoint is committed yet
because the license-reviewed multi-domain dataset snapshot is not present.

After both checkpoints exist, `scripts/evaluate_multidomain.py` evaluates them on the same held-out
records, reports per-domain condition accuracy, and saves potential false negatives for manual review.

This model is for inspection triage. It cannot confirm cracks, corrosion, structural weakness, material
integrity, chemical contamination, coral death, fish population size, or deployment safety. False
negatives must be reviewed before any field trial.
