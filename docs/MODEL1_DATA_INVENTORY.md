# Model 1 Data Inventory

## Inventory decision

**Zero approved training or evaluation images are present.** The repository contains governance schemas and
source research, not a Model 1 dataset snapshot. This is the primary freeze blocker.

| Artifact | State | Count / role | Included in Model 1 metrics? |
|---|---|---:|---|
| `dataset/manifests/approved_assets.csv` | Present; header only | 0 approved assets | No |
| `dataset/manifests/raw_assets.csv` | Present; header only | 0 raw assets | No |
| `dataset/manifests/rejected_assets.csv` | Present; header only | 0 rejected assets | No |
| `dataset/processed/labels.csv` | Missing | canonical labels expected by scripts | No |
| `dataset/annotations/bboxes.json` | Missing | canonical detection annotations | No |
| `dataset/processed/labels.example.csv` | Schema example | 1 non-existent example row | No |
| `dataset/annotations/bboxes.example.json` | Schema example | illustrative annotation | No |
| `dataset/sources.yaml` | Present | source-policy registry | No |

## Required snapshot properties

- Every image must map to an approved source record, license URL, attribution, download timestamp, and SHA-256.
- Splits must be mission/video/site-disjoint; adjacent video frames and duplicates cannot cross splits.
- Real and synthetic data must be explicitly marked. Synthetic frames may augment training but cannot be the
  sole test evidence for open-sea performance.
- Domain, primary label, anomaly state, visibility, and inspection metadata must use the canonical schema.
- Unclear-license assets remain research candidates and must not be downloaded into the approved snapshot.

## Current class and split counts

Train, validation, and test counts are all **N/A**, not zero-class performance measurements, because no
canonical manifest exists. Per-class and per-domain distributions cannot be computed. The source candidates
and their proposed roles are recorded separately in `MODEL1_DATASET_EXPANSION_MAP.md`; candidates do not count
as acquired or approved data.

## Reproducible inventory command

After acquisition, run:

```powershell
python scripts/validate_image_dataset.py dataset/processed/labels.csv `
  --boxes dataset/annotations/bboxes.json `
  --report outputs/model1_audit/dataset_validation.json
```

The current invocation fails because the canonical labels file is missing. That failure is preserved in the
freeze report and machine-readable blocker record.
