# Model card: OceanSense perception v1

The supported classifier is ImageNet-pretrained EfficientNet-B0 with a seven-class output head. The
optional detector is YOLOv8n and must only be trained when genuine bounding-box annotations exist.

Training and evaluation code reports test accuracy, per-class precision/recall/F1, a confusion matrix,
and 20 JSON-compatible sample predictions. No trained image checkpoint is committed yet because the
license-reviewed dataset snapshot is not present.

This model is for inspection triage. It cannot confirm cracks, corrosion, structural weakness, material
integrity, or deployment safety. False negatives must be reviewed before any field trial.
