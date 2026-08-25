# Model 1 Checkpoint Recovery Decision

**Decision date:** 2026-08-25

**Branch audited:** `codex/rov-digital-twin`

**Scope:** checkpoint recovery decision and new-baseline gate only; no training, dataset download, Model 2, or Twin 2 work

## 1. Final Decision

**CHECKPOINTS NOT RECOVERED**

Neither required visual Model 1 checkpoint exists at its canonical path, under an equivalent filename in the reasonable local/project locations searched, in the repository's reachable or recoverable Git history, or in the reviewed archives. The only OceanSense `.pt` and `.onnx` weights found are Unity ML-Agents PPO navigation policies. They are not RGB EfficientNet-B0 domain/condition classifiers and are explicitly rejected.

Original Model 1 validation is therefore **not possible with the evidence currently available**. Model 1 remains blocked and is not frozen. If the original package is not supplied by the recovery deadline in Section 5, the project must treat subsequent training as a **new Model 1 baseline**, with a new identity and new evidence chain—not as validation or recreation of the original trained model.

## 2. Expected Checkpoints

| Expected File | Required? | Evidence Source | Found? | Notes |
|---|---:|---|---:|---|
| `models/oceansense_domain_efficientnet_b0.pt` | Yes | `README.md`, `docs/integration_guide.md`, `scripts/evaluate_multidomain.py`, `scripts/train_classifier.py` | No | Must be a PyTorch checkpoint dictionary for task `domain`, with the canonical six-domain class order, compatible EfficientNet-B0 state dictionary, version, and provenance metadata. |
| `models/oceansense_condition_efficientnet_b0.pt` | Yes | `README.md`, `docs/integration_guide.md`, `scripts/evaluate_multidomain.py`, `scripts/train_classifier.py` | No | Must be a PyTorch checkpoint dictionary for task `condition`, with the canonical nine-condition class order, compatible EfficientNet-B0 state dictionary, version, and provenance metadata. |

Both files are mandatory for the multi-domain evaluator. Finding only one would change the decision to partially recovered but would still leave original evaluation blocked.

## 3. Search Evidence

### 3.1 Folders searched

The search was rerun specifically for the exact filenames and reasonable equivalents across:

- current repository, including ignored `results/`, Unity assets, hidden files, and the `models/` directory;
- `C:/Users/Kerem/OneDrive`, including Documents/ChatGPT projects and Desktop project folders;
- `C:/Users/Kerem/Downloads`, regular Desktop/Documents, and project source folders;
- `C:/Users/Kerem/.codex/attachments`;
- the broader user profile, excluding dependency/package caches such as AppData, Conda, NuGet, `.venv`, `site-packages`, `node_modules`, and Unity `Library/PackageCache`.

The broad user-profile filename scan returned no file whose name plausibly combined OceanSense/Model 1, EfficientNet, and domain/condition checkpoint terms.

### 3.2 Git refs and recoverable objects

- Inspected all local/remote refs with `git for-each-ref`; the only project branch is `codex/rov-digital-twin` and its matching origin ref. A Codex turn-diff base ref was also included in object traversal.
- Searched all reachable objects with `git rev-list --objects --all`.
- Inspected tags and stashes: none exist.
- Inspected the reflog and the amended unreachable commit.
- Ran `git fsck --full --unreachable --no-reflogs`. The 154 unreachable blobs were size-checked; the largest is 186,193 bytes, far below a normal EfficientNet-B0 state dictionary, and the only unreachable commit tree contains the same two Unity navigation ONNX files rather than visual checkpoints.

No Git object or historical path contains either expected checkpoint or an equivalent visual checkpoint.

### 3.3 Archives searched

Twenty-six reasonable ZIP archives under Downloads, Desktop/Documents, ChatGPT project locations, and Codex attachments were inspected by reading their central directories without extraction. The scan included the prior repository export and recent transfer/WhatsApp/Drive-style archives; unrelated package/dependency and school-book archives were excluded.

The only relevant repository archive was:

- `C:/Users/Kerem/Downloads/rov-digital-twin-codex-rov-digital-twin.zip`

It contains empty asset-manifest templates and `unity/Assets/ROVDigitalTwin/Models/OceanSenseROV_Bootstrap.onnx`, but no visual `.pt`, `.pth`, `.ckpt`, or equivalent exported domain/condition model. No archive member matched the two exact filenames.

### 3.4 Filename and content patterns

Patterns included:

- exact `oceansense_domain_efficientnet_b0.pt` and `oceansense_condition_efficientnet_b0.pt`;
- combinations of `oceansense`, `model1`, `domain`, `condition`, `efficientnet`, `checkpoint`, `weight`, and `baseline`;
- model formats `.pt`, `.pth`, `.ckpt`, `.bin`, `.safetensors`, `.onnx`, `.pb`, `.h5`, and `.tflite`;
- textual references to the expected paths and model versions.

Text references point only to the missing canonical paths or intended commands; no alternate storage path or hash of an original checkpoint was found.

### 3.5 Candidate files found and disposition

| Candidate | Evidence | Valid? | Rejection reason |
|---|---|---:|---|
| `results/oceansense_navigation_v3/OceanSenseROV/OceanSenseROV-250081.pt` and related run `.pt` files | A safe PyTorch metadata read shows top-level keys `Policy`, `global_step`, `Optimizer:value_optimizer`, and `Optimizer:critic` | No | ML-Agents policy/trainer state; lacks required `state_dict`, `labels`, `task`, `model_version`, and Model 1 data metadata. |
| `results/oceansense_*/OceanSenseROV.onnx` | ONNX inspection shows input `obs_0` shaped `[batch,39]` and output `continuous_actions` shaped `[batch,8]` | No | Navigation/control policy with 39 vector observations and 8 continuous thruster actions; not RGB 224-pixel, 6/9-class visual classification. |
| `unity/Assets/ROVDigitalTwin/Models/OceanSenseROV_Bootstrap.onnx` | Unity docs/config identify behavior `OceanSenseROV` and PPO | No | Navigation ONNX; hard rule prohibits treating navigation/control ONNX as visual Model 1. |
| `unity/Assets/ROVDigitalTwin/Models/OceanSenseROV_OpenSea_Experimental.onnx` | Same SHA-256 as the navigation-v3 exported ONNX and same Unity behavior contract | No | Navigation ONNX, not an EfficientNet visual checkpoint. |
| `models/weakpoint_v2.json` and weak-point metrics | Telemetry feature/model schema and vehicle-health labels | No | Non-visual telemetry classifier; wrong serialization, inputs, labels, and task. |
| `data/predictions_sample.jsonl`, fixture classifiers, and failure-index header | Files self-identify as sample/fixture or contain no rows | No | Test scaffolding/placeholder evidence, not learned weights. |
| LLM adapters, optimizer/scheduler/rng `.pt`, and Safetensors in other local projects | Enclosing projects and artifact roles identify language-model training | No | Unrelated architecture/task and no OceanSense visual provenance. Renaming is prohibited. |

No random ImageNet initialization or incomplete visual state dictionary was found. If one appears later, it must still be rejected unless the entire load contract and provenance checks in Section 4 pass.

## 4. Model Loading Contract

### 4.1 Loader and evaluator

- `scripts/evaluate_multidomain.py` accepts `--domain-checkpoint` and `--condition-checkpoint`, then constructs `TorchvisionDomainClassifier` and `TorchvisionEfficientNetClassifier`.
- `src/oceansense/perception.py` loads each path with `torch.load`, reads the payload, constructs `torchvision.models.efficientnet_b0(weights=None)`, replaces its final linear layer with the payload label count, loads `payload["state_dict"]`, and applies the default ImageNet EfficientNet-B0 inference transform to RGB input.
- `scripts/train_classifier.py` is the producer contract and saves a dictionary with `state_dict`, `labels`, `task`, `model_version`, and `metadata`.

### 4.2 Expected format and classes

| Property | Domain checkpoint | Condition checkpoint |
|---|---|---|
| Serialization | PyTorch `.pt` dictionary | PyTorch `.pt` dictionary |
| Architecture | Torchvision EfficientNet-B0 | Torchvision EfficientNet-B0 |
| Input | RGB image, default EfficientNet transform, nominal 224-pixel config | RGB image, default EfficientNet transform, nominal 224-pixel config |
| Expected task | `domain` | `condition` |
| Expected class count | 6 canonical domain classes | 9 canonical condition classes |
| Required payload keys | `state_dict`, `labels`, `task`, `model_version`, `metadata` | Same |
| Required provenance | checkpoint SHA-256, data-manifest SHA-256, config/version and original run evidence | Same |

The current loader rejects a domain task passed to the condition adapter, a non-domain task passed to the domain adapter, unsupported labels, and incompatible state dictionaries. A valid recovery check must be stricter than merely loading: class sets **and order**, full expected class counts, model/version metadata, manifest/config hashes, and original-run provenance must match.

### 4.3 Both checkpoints and missing-file behavior

Both checkpoints are required by the evaluator. With the current missing `labels.csv`, evaluation fails during label loading before reaching model construction. Once labels exist, a missing checkpoint raises `FileNotFoundError` from `torch.load`. A malformed payload raises `KeyError`; task/label mismatch raises `ValueError`; an incompatible state dictionary raises a PyTorch load error. Placeholder, random, partial, renamed, navigation, or newly trained weights cannot validate the original Model 1.

## 5. Recovery Feasibility

### Is recovery realistic?

**Not from the currently available repository, local project folders, Git database, or reviewed archives.** One final owner-led recovery attempt remains realistic because trained weights may have stayed on the original training machine or in unsynchronized external storage. Recovery probability falls sharply if the original trainer cannot identify a run directory, cloud notebook output, artifact store, or backup.

### Likely holder and exact request

The likely holder is the person who ran `scripts/train_classifier.py` or the predecessor training notebook/script. They should check the original workstation, external drives, cloud drive trash/version history, Colab/Kaggle session exports, experiment tracking artifacts, release assets, and teammate handoff folders.

Send this exact request immediately:

> Do you have these two files: `oceansense_domain_efficientnet_b0.pt` and `oceansense_condition_efficientnet_b0.pt`, plus the exact dataset manifest, `labels.csv`, immutable split, training/evaluation config and commands, complete metrics/predictions, environment record, and SHA-256 hashes? Please send the original files without renaming or re-saving them, and identify the machine/run/date they came from.

The minimum recovery package is:

1. both original `.pt` files;
2. original approved asset manifest and license/access evidence;
3. exact `labels.csv` and image snapshot reference;
4. immutable train/validation/test split or run manifest;
5. training and evaluation command/config;
6. full metrics, predictions, failure examples, and logs;
7. Python/Torch/Torchvision environment versions;
8. SHA-256 hashes and original run/machine/date/provenance.

### Deadline

Set a hard recovery deadline of **2026-09-01 at 17:00 Europe/Istanbul** (five business days). Preserve any response, including “not found,” in the project evidence log. If the complete pair and provenance package are not received and validated by that time, stop searching the same local sources, keep the original model blocked, and authorize a new-baseline plan.

## 6. If Checkpoints Are Not Recovered

The next path is a **new Model 1 baseline**, not validation of the original Model 1. Training is not authorized by this report.

### Gate A — approved data and labels

1. Complete dataset permission requests and asset-level governance described in `docs/MODEL1_MINIMAL_EVALUATION_SET_PLAN.md`.
2. Build a rights-cleared development dataset for training/validation, plus the independently locked minimum evaluation snapshot. The 270-image external evaluation set must not be used for training, threshold selection, or model selection.
3. Create a real `labels.csv` with every field enforced by `src/oceansense/data.py`; require dual review and adjudication.
4. Ensure all six domain and nine condition classes have adequate, source-diverse training support. Do not train a “full” baseline with missing classes.

### Gate B — immutable split and manifests

1. Split development data by `mission_or_video_id`/site/source group with seed 42; never split adjacent frames across train/validation/test.
2. Freeze the development labels, approved-asset manifest, group-aware split, class order, preprocessing config, and checksums before training.
3. Lock the independent `model1_min_eval_v1` evaluation snapshot separately and keep it unseen until the final baseline is selected.
4. Materialize ImageFolder trees only from the locked labels and verify that domain and condition trees share the same sample IDs/splits.

Preflight commands, after approved files exist:

```powershell
python scripts/validate_image_dataset.py dataset/processed/model1_baseline_v2_labels.csv `
  --report outputs/evaluation_reports/model1_baseline_v2_dataset_validation.json

python scripts/prepare_imagefolders.py `
  --labels dataset/processed/model1_baseline_v2_labels.csv `
  --output dataset/imagefolders/model1_baseline_v2 `
  --mode copy
```

If a split does not yet exist, it may be created once with `scripts/split_image_dataset.py --seed 42`, reviewed for group leakage, and then frozen. The current splitter groups by `mission_or_video_id`, but a manual audit must also verify site/source independence.

### Gate C — new model identity and training commands

Before training, authorize a new baseline identifier such as `model1_baseline_v2`; update the training metadata/version output so the payload cannot be confused with the missing original `*_v1` model. Do not overwrite or backfill the original canonical evidence.

Required future training commands:

```powershell
python scripts/train_classifier.py `
  --task domain `
  --data dataset/imagefolders/model1_baseline_v2/domain `
  --output models/oceansense_domain_efficientnet_b0_v2.pt `
  --report outputs/evaluation_reports/model1_baseline_v2_domain_metrics.json `
  --epochs <predeclared> --batch-size <predeclared> --seed 42 `
  --class-balance weighted_loss --weights imagenet `
  --data-manifest dataset/manifests/model1_baseline_v2_approved_assets.csv

python scripts/train_classifier.py `
  --task condition `
  --data dataset/imagefolders/model1_baseline_v2/condition `
  --output models/oceansense_condition_efficientnet_b0_v2.pt `
  --report outputs/evaluation_reports/model1_baseline_v2_condition_metrics.json `
  --epochs <predeclared> --batch-size <predeclared> --seed 42 `
  --class-balance weighted_loss --weights imagenet `
  --data-manifest dataset/manifests/model1_baseline_v2_approved_assets.csv
```

Replace the angle-bracketed hyperparameters only through a reviewed, committed training config **before** viewing locked-test results. These commands are documented, not executed.

### Gate D — held-out evaluation

After training/model selection is complete and checkpoint hashes are frozen, run the new pair on the independent approved evaluation snapshot:

```powershell
python scripts/evaluate_multidomain.py `
  --labels dataset/processed/model1_min_eval_v1/labels.csv `
  --domain-checkpoint models/oceansense_domain_efficientnet_b0_v2.pt `
  --condition-checkpoint models/oceansense_condition_efficientnet_b0_v2.pt `
  --output outputs/evaluation_reports/model1_baseline_v2_multidomain_metrics.json
```

The evaluation must export a complete prediction ledger in addition to the current 20-sample preview before any freeze review.

### Gate E — evidence required before freeze

At minimum, record:

- dataset/manifest/split/config/checkpoint SHA-256 hashes and environment versions;
- domain accuracy and condition accuracy;
- macro F1, balanced accuracy, and expected calibration error;
- per-class precision, recall, F1, support, and confusion matrices for all 6/9 classes;
- per-domain condition accuracy and breakdowns by source, visibility, and real/synthetic origin;
- safety-relevant false negatives, high-confidence `unknown` errors, complete predictions, and reviewed failure examples;
- training/validation loss and accuracy history, final model-selection rule, and evidence that the locked evaluation set was not used for tuning;
- limitations and claim boundaries.

Numerical freeze thresholds must be predeclared by the project owner and reviewer before opening final held-out results. Evidence existence alone does not guarantee a freeze. Freeze is allowed only after the complete report, failure review, provenance checks, and predeclared thresholds pass.

## 7. Recommended Next Action

**Request checkpoint package from owner.**

Send the exact request in Section 5 now and apply the 2026-09-01 17:00 Europe/Istanbul deadline. In parallel, proceed with dataset permission requests because both the original evaluation path and a new baseline require approved data. If recovery fails at the deadline, keep the original Model 1 blocked and begin a separately authorized new Model 1 baseline training plan; do not train under the original identity.

## Search Commands and Integrity Statement

Representative read-only checks included `Test-Path`, `rg --files -uu`, `rg -n`, `git for-each-ref`, `git rev-list --objects --all`, `git reflog --all`, `git fsck --full --unreachable --no-reflogs`, `git cat-file --batch-check`, `git ls-tree`, archive central-directory inspection through .NET, SHA-256/size inspection, safe PyTorch payload-key inspection, and ONNX input/output inspection. Repository configs/scripts/recovery reports were read directly.

No Model 1 training was performed. No fake, placeholder, random, renamed, or incomplete checkpoint was created. No external dataset was downloaded. No navigation/control ONNX was accepted as a visual checkpoint. No Model 1 architecture, Model 2, or Twin 2 file was changed. Model 1 is not frozen.
