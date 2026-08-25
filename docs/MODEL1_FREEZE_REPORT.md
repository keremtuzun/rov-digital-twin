# Model 1 Freeze Report

## Executive Decision

**Blocked.** Model 1 is not frozen. This is an evidence decision, not a quality judgement about an unmeasured
model. The repository has conventional visual-perception training and evaluation code, but no approved image
dataset, trained visual checkpoint, immutable split manifest, prediction export, or metrics.

## Repository Artifacts

| Item | Path / audited state |
|---|---|
| Source files | `src/oceansense/perception.py`, `src/oceansense/underwater_augmentation.py` |
| Training | `scripts/train_classifier.py`, domain/condition wrappers, `scripts/train_detector.py` |
| Evaluation | `scripts/evaluate_multidomain.py` |
| Checkpoint | intended domain and condition `.pt` paths are missing; no approved detector checkpoint |
| Config | `config/model_config.yaml`, SHA-256 `8AC8A3DD577A00F6AED0F01CD2C7B0C94415EB097C3640610C7C7BF261126B9C` |
| Label schema | `config/labels.yaml`, SHA-256 `E8619EFAA14DEFFD267F9062282408CF419B719F360462BB37141C25BF36680A` |
| Dataset | `dataset/processed/labels.csv` and `dataset/annotations/bboxes.json` are missing |
| Splits | `dataset/imagefolders/domain` and `dataset/imagefolders/condition` are missing |
| Approved manifest | `dataset/manifests/approved_assets.csv`, header only, 0 approved assets |
| Metrics path | intended `outputs/evaluation_reports/multidomain_metrics.json`, missing |
| Failure index | `outputs/model1_audit/failure_index.csv`, schema header only |

The `.example` files are schemas only and are excluded from counts. The telemetry weak-point model and Unity
navigation policies are different components and are not Model 1 evidence.

## Architecture / Design

- **Model family/framework:** two Torchvision EfficientNet-B0 classifiers; optional Ultralytics YOLOv8n
  detector only when defensible boxes exist.
- **Task type:** inspection-domain classification plus visible-condition classification; optional detection.
- **Input modality:** RGB still image; ImageFolder train/validation/test layout for training.
- **Input size and preprocessing:** configured 224 x 224 RGB input and EfficientNet-B0 weights-defined
  resize/crop/normalization.
- **Output type:** domain class/confidence, condition class/confidence/top-k/uncertainty, optional boxes and
  confidence. Visual indicators do not confirm physical failure.
- **Domain labels:** `structure`, `nature_ecology`, `contamination`, `fishing_aquaculture`,
  `general_underwater`, `unknown`.
- **Condition labels:** `normal_or_no_visible_concern`, `possible_structural_concern`, `biofouling`,
  `marine_debris`, `poor_visibility`, `ecological_stress_indicator`, `fish_or_habitat_activity`,
  `aquaculture_infrastructure_concern`, `unknown`.
- **Checkpoint format/version:** PyTorch `.pt` payload with state dict, task, labels and provenance metadata;
  configured versions `domain_efficientnet_b0_v1` and `condition_efficientnet_b0_v1`.
- **Training configuration in code:** AdamW, learning rate `3e-4`, defaults of 10 epochs, batch size 16 and seed
  42, deterministic algorithms, weighted loss, optional ImageNet initialization.
- **Inference configuration:** CPU default, EfficientNet softmax/top-k, image-quality uncertainty/unknown
  abstention; optional YOLO confidence 0.25.
- **Limitations:** single-frame RGB cannot establish hidden state; no temporal/sonar fusion; broad visible
  condition classes; no actual checkpoint calibration.

## Metrics

| Metric | Result | Evidence |
|---|---:|---|
| Overall precision / recall / F1 | N/A | no held-out predictions |
| Accuracy / balanced accuracy | N/A | no checkpoint or test split |
| mAP / detector metric | N/A | no approved detector or boxes |
| Per-class metrics / confusion matrix | N/A | no evaluation run |
| False-positive / false-negative rate | N/A | no reviewed predictions |
| Robustness by environment | N/A | no immutable metadata slices |
| Latency / throughput / model size | N/A | no deployable checkpoint |

No project-owned thresholds were found. This is a **proposed baseline-review table, not a deployment or safety
gate**: macro F1 >= 0.70 on mission-disjoint real test data; recall >= 0.80 for
`possible_structural_concern` and `poor_visibility`; expected calibration error <= 0.10; high-confidence known
labels on unknown/OOD <= 5%. Latency must be measured and gated only on named target hardware. These proposals
require product/safety-owner approval and must not be tuned on the test split.

## Dataset Used

- **Training, validation and test:** unavailable; zero approved assets and no immutable splits.
- **Preprocessing/augmentation declared by code:** `underwater_physical_aug_v1` applies bounded color
  attenuation, contrast/brightness change, optional blur, light hotspot, particles, small occlusion and JPEG
  degradation to training images; evaluation uses the EfficientNet default transform.
- **Known limitations:** provenance, class counts, split integrity, label quality and real/synthetic separation
  cannot be measured.

See `docs/MODEL1_DATA_INVENTORY.md`. External candidates are research only and are not data used.

## Failure Summary

Empirical top failure modes are **Blocked** because there are no predictions or licensed examples. The
taxonomy covers all guide-required categories. Example/index path:
`outputs/model1_audit/failure_index.csv` (header only).

## Reproducibility

Audited branch `codex/rov-digital-twin`, baseline commit
`6c14eb0e288343ec0705c74af776548ef1615cea`, Python `3.13.14`.

```powershell
python scripts/validate_image_dataset.py dataset/processed/labels.csv `
  --boxes dataset/annotations/bboxes.json `
  --report outputs/model1_audit/dataset_validation.json

python scripts/evaluate_multidomain.py `
  --labels dataset/processed/labels.csv `
  --domain-checkpoint models/oceansense_domain_efficientnet_b0.pt `
  --condition-checkpoint models/oceansense_condition_efficientnet_b0.pt `
  --output outputs/evaluation_reports/multidomain_metrics.json
```

Both commands exit `1` at the missing labels file. The audit environment has `torch` but lacks `torchvision`
and `ultralytics`; install `.[vision,detection]` for a future authorized run. Seed 42 is a code default; no
trained run/seed is claimed.

## Decision Rationale

Checkpoint, source-approved data, train/validation/test splits and metrics do not exist. API fixtures validate
integration only. Therefore the only supported decision is **Blocked**, not Frozen or Not Frozen.

## Next Step

Approve licenses and populate the asset manifest with hashes; build and validate a mission/video-disjoint
snapshot; then locate the intended checkpoint or separately authorize a named training candidate. Run held-out
evaluation, populate the failure index, measure target-hardware latency, and repeat this gate.
