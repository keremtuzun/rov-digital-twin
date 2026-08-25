# Model 1 Freeze Report

## Executive decision

**BLOCKED — Model 1 is not frozen.**

This is an evidence decision, not a quality judgement about an unmeasured model. The repository has the
training and evaluation implementation for a conventional visual Model 1, but the reviewed commit has no
approved image dataset, trained visual checkpoint, immutable split manifest, prediction export, or metrics.
The telemetry weak-point model and Unity PPO navigation policies are different components and cannot be
used as Model 1 evidence.

## Audited baseline

| Item | Audited value |
|---|---|
| Git branch | `codex/rov-digital-twin` |
| Git commit | `65cf3ba9bca486f4bc3c19ee01b7831a802cc652` |
| Python | `3.13.14` |
| Model config | `config/model_config.yaml`, SHA-256 `8AC8A3DD577A00F6AED0F01CD2C7B0C94415EB097C3640610C7C7BF261126B9C` |
| Label schema | `config/labels.yaml`, SHA-256 `E8619EFAA14DEFFD267F9062282408CF419B719F360462BB37141C25BF36680A` |
| Approved manifest | `dataset/manifests/approved_assets.csv`, header only, zero approved assets |
| Intended labels | `dataset/processed/labels.csv`, missing |
| Intended boxes | `dataset/annotations/bboxes.json`, missing |
| Domain checkpoint | `models/oceansense_domain_efficientnet_b0.pt`, missing |
| Condition checkpoint | `models/oceansense_condition_efficientnet_b0.pt`, missing |
| Detector checkpoint | no approved path or artifact |
| Evaluation output | `outputs/evaluation_reports/multidomain_metrics.json`, missing |

The `.example` label and bounding-box files are schema examples only. They are not observations and are
excluded from counts. `src/oceansense/perception.py` implements the EfficientNet classifiers and optional
Ultralytics detector. `scripts/train_classifier.py` and its domain, condition, and detector wrappers are
training entry points; `scripts/evaluate_multidomain.py` is the intended review entry point.

## Reproduction evidence

Run from the repository root:

```powershell
python scripts/validate_image_dataset.py dataset/processed/labels.csv `
  --boxes dataset/annotations/bboxes.json `
  --report outputs/model1_audit/dataset_validation.json
```

Observed result: exit code `1`, because `dataset/processed/labels.csv` does not exist.

```powershell
python scripts/evaluate_multidomain.py `
  --labels dataset/processed/labels.csv `
  --domain-checkpoint models/oceansense_domain_efficientnet_b0.pt `
  --condition-checkpoint models/oceansense_condition_efficientnet_b0.pt `
  --output outputs/evaluation_reports/multidomain_metrics.json
```

Observed result: exit code `1`, at the same missing labels file. The installed audit environment also lacks
`torchvision` and `ultralytics`; those dependencies must be installed from the project lock/requirements
before a future training or evaluation run.

## Metrics

| Measure | Result | Reason |
|---|---:|---|
| Accuracy | N/A | no checkpoint, labels, or held-out predictions |
| Macro precision / recall / F1 | N/A | no evaluation run |
| Per-class precision / recall / F1 | N/A | no evaluation run |
| Confusion matrix | N/A | no evaluation run |
| Robustness by visibility/domain | N/A | no immutable subset assignments |
| Latency and throughput | N/A | no deployable Model 1 checkpoint |

No threshold is retroactively selected and no metric is inferred from fixture responses. When checkpoint
environment variables are absent, `src/oceansense/api.py` uses fixture classifiers. That behavior supports
API development but is not Model 1 validation evidence.

## Freeze gate and smallest next action

1. Approve source licenses and populate `approved_assets.csv` with real file hashes.
2. Build a mission/video-disjoint immutable train/validation/test manifest; validate it with the command above.
3. Locate the intended existing Model 1 checkpoint or, under separate authorization, train a named candidate.
4. Record checkpoint/config/data hashes and run the exact held-out evaluation.
5. Review false positives and negatives, populate the failure index, measure latency, then repeat this decision.

Until all five are complete, reports and APIs must describe Model 1 as **blocked / unavailable**, never as a
frozen production classifier.
