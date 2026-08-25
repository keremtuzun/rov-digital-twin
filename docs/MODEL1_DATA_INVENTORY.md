# Model 1 Data Inventory

## Dataset Summary

**Zero approved training, validation or test images are present.** The repository contains governance schemas
and source research, not a Model 1 dataset snapshot.

| Name | Path/URL | License | Modality | Samples | Labels | Split | Real/Synthetic | Notes |
|---|---|---|---|---:|---|---|---|---|
| Approved asset manifest | `dataset/manifests/approved_assets.csv` | per-row required | image metadata | 0 | schema fields | none | mixed-capable | header only |
| Raw asset manifest | `dataset/manifests/raw_assets.csv` | per-row required | image metadata | 0 | schema fields | none | mixed-capable | header only |
| Rejected asset manifest | `dataset/manifests/rejected_assets.csv` | per-row required | image metadata | 0 | rejection metadata | none | mixed-capable | header only |
| Canonical labels | `dataset/processed/labels.csv` | per-row required | RGB references | unavailable | canonical class/metadata | missing | explicit flag required | file missing |
| Canonical boxes | `dataset/annotations/bboxes.json` | per-row required | RGB boxes | unavailable | boxes/classes | missing | explicit flag required | file missing |
| Label example | `dataset/processed/labels.example.csv` | `review_required` | schema only | 0 usable | illustrative row | example | stated non-synthetic | referenced image absent; excluded |
| Box example | `dataset/annotations/bboxes.example.json` | example only | schema only | 0 usable | illustrative box | example | example | excluded |
| Source registry | `dataset/sources.yaml` | policy metadata | source metadata | 7 source families | none | candidate | mixed | not acquired data |

## Dataset Use Decisions

- **Training:** none documented or present; retraining is not authorized by this review.
- **Validation:** none; model selection history cannot be reconstructed.
- **Test:** none; no freeze evaluation is possible.
- **Twin 1-generated:** no committed image set. Twin 1 can produce PNG plus JSON metadata and must label it
  synthetic/fixture/demo; it is not safe as sole real validation/test evidence.
- **External candidates:** documented only in `MODEL1_DATASET_EXPANSION_MAP.md`; no candidate is approved or used.

## Split Integrity

- **Train count:** N/A
- **Validation count:** N/A
- **Test count:** N/A
- **Overlap check:** Blocked because no canonical manifest/splits exist.

Future splits must be mission/video/site-disjoint. Adjacent frames, source duplicates and synthetic parent
derivatives cannot cross splits. The test split must remain untouched by threshold tuning.

## Label Inventory

- **Domain classes:** `structure`, `nature_ecology`, `contamination`, `fishing_aquaculture`,
  `general_underwater`, `unknown`.
- **Condition classes:** `normal_or_no_visible_concern`, `possible_structural_concern`, `biofouling`,
  `marine_debris`, `poor_visibility`, `ecological_stress_indicator`, `fish_or_habitat_activity`,
  `aquaculture_infrastructure_concern`, `unknown`.
- **Class counts:** N/A; zero approved assets is not a performance/class distribution.
- **Known label issues:** broad visible-condition aliases collapse crack/corrosion into
  `possible_structural_concern`; no reviewer agreement, severity or boundary audit exists.

## Preprocessing and Augmentation

- **Preprocessing:** RGB conversion and Torchvision EfficientNet-B0 default weights transform; configured
  input size 224.
- **Augmentation:** training-only `underwater_physical_aug_v1`, probability 0.75: bounded channel attenuation,
  contrast/brightness, optional Gaussian blur, light hotspot, particles, small partial occlusion and JPEG
  degradation. No evidence shows it was used in an actual training run.

## Data Risks

- **Domain gaps:** no real underwater infrastructure test set; no verified crack/weld/bolt/coating coverage;
  no visibility, distance, viewpoint, sea-state or site strata.
- **License/access risks:** every asset needs source URL, license URL, attribution, timestamp and SHA-256;
  unclear-license candidates cannot be downloaded into the approved snapshot.
- **Missing metadata:** mission/video/site IDs, frame timestamps, reviewer/adjudication, split role, class counts,
  real/synthetic provenance and acquisition conditions.

## Freeze Impact

The data does **not** support freezing Model 1. The missing approved snapshot and train/validation/test separation
are serious blockers. After acquisition, validate with:

```powershell
python scripts/validate_image_dataset.py dataset/processed/labels.csv `
  --boxes dataset/annotations/bboxes.json `
  --report outputs/model1_audit/dataset_validation.json
```
