# Model 1 Evidence Recovery Report

Audit date: 2026-08-25  
Branch: `codex/rov-digital-twin`  
Audited commit: `cefc3fc5eeae180e502aa9df6d537ae6ecd97253`

## 1. Executive Decision

**PARTIALLY EVALUABLE.** The repository contains a coherent visual Model 1 implementation, canonical class
schema, model/preprocessing configuration, dataset governance, split tooling, and an evaluation script. It does
not contain the trained visual checkpoints, approved image/label snapshot, materialized train/validation/test
split, or genuine Model 1 metrics/predictions required to run a meaningful baseline evaluation today.

This decision does not authorize training and does not change the existing freeze decision: Model 1 remains
**Blocked / not frozen**.

## 2. Evidence Table

| Required Item | Found? | Evidence Path / Command | Notes |
|---|---:|---|---|
| Checkpoint / weights | No | `Test-Path models/oceansense_domain_efficientnet_b0.pt` and condition/detector equivalents returned `False`; `git rev-list --objects --all` found no visual `.pt/.pth/.ckpt` | `models/weakpoint_v2.json` is telemetry diagnostics. Unity and ignored `results/` `.pt/.onnx` files are ML-Agents navigation policies, confirmed by `docs/rl_policy_model_card.md` and PPO configs. |
| Label schema / `labels.csv` | Partial | `config/labels.yaml`; `dataset/processed/labels.example.csv`; missing `dataset/processed/labels.csv` | Canonical domain/condition vocabulary and schema example exist; no actual labelled records. |
| Training dataset reference | Partial | `dataset/sources.yaml`; `dataset/README.md`; `dataset/manifests/approved_assets.csv` | Source/governance plan exists, but all three asset manifests contain headers only: 0 approved/raw/rejected assets. No dataset version used for training is identified. |
| Validation/test dataset reference | No | Missing `dataset/processed/labels.csv`, images and evaluation snapshot | Documentation defines intended roles, but no actual validation/test asset or version exists. |
| Split definition | Partial | `scripts/split_image_dataset.py`; `scripts/prepare_imagefolders.py`; `src/oceansense/data.py` | Deterministic seed-42 split/materialization code exists. No materialized `dataset/imagefolders/{domain,condition}` or immutable split manifest exists. |
| Evaluation command/script | Yes | `scripts/evaluate_multidomain.py`, SHA-256 `FE6F6AF96C9A3523527C47A04104C9D24347F8597936BDEF825CCD8EEF656482` | Requires labels plus domain and condition checkpoints; reports domain/condition accuracy, macro F1, calibration, breakdowns, samples and false negatives. |
| Existing metrics | No | Intended `outputs/evaluation_reports/multidomain_metrics.json` is absent | `artifacts/training_metrics.json` and `artifacts/training/weakpoint_v2_metrics.json` use vehicle-fault labels and are telemetry-model metrics. PPO metrics are navigation metrics. None is visual Model 1 evidence. |
| Prediction outputs/failure cases | Partial | `data/predictions_sample.jsonl`; `outputs/model1_audit/failure_index.csv` | Sample rows explicitly say `sample-not-a-result` / `fixture-model1`; failure index has only a header. No genuine checkpoint predictions. |
| Model config | Yes | `config/model_config.yaml`, SHA-256 `8AC8A3DD577A00F6AED0F01CD2C7B0C94415EB097C3640610C7C7BF261126B9C` | Defines two EfficientNet-B0 classifiers and optional YOLOv8n detector. |
| Preprocessing config | Yes | `src/oceansense/perception.py`; `src/oceansense/underwater_augmentation.py`, SHA-256 `1150204DBC000B8548317A521D7B574A519DB5AC7C55E2EABB76A1912C9F316` | EfficientNet default inference transforms and seeded bounded underwater training augmentation are implemented. |
| License/access notes | Yes | `dataset/sources.yaml`; `dataset/licenses/README.md`; `dataset/licenses/noaa_ocean_exploration_2026-08-23.txt` | Source/per-asset policy and manual-review cases are documented. No third-party dataset was downloaded in this audit. |

## 3. Model 1 Architecture Summary

- **Model family/framework:** Torchvision EfficientNet-B0 for domain classification and condition
  classification; optional Ultralytics YOLOv8n detector when reviewed boxes exist.
- **Task type:** two single-image classifiers plus optional object detection.
- **Input modality:** RGB image files. Training expects ImageFolder trees for `train`, `val`, and `test`.
- **Input shape/preprocessing:** `config/model_config.yaml` declares 224 input size. Inference converts to RGB and
  uses `EfficientNet_B0_Weights.DEFAULT.transforms()`.
- **Outputs:** inspection domain class/confidence; visible condition class/confidence/top-k/uncertainty;
  optional label/confidence/bounding box detections.
- **Domain classes:** `structure`, `nature_ecology`, `contamination`, `fishing_aquaculture`,
  `general_underwater`, `unknown`.
- **Condition classes:** `normal_or_no_visible_concern`, `possible_structural_concern`, `biofouling`,
  `marine_debris`, `poor_visibility`, `ecological_stress_indicator`, `fish_or_habitat_activity`,
  `aquaculture_infrastructure_concern`, `unknown`.
- **Augmentation defaults:** `UnderwaterAugmentation` version `underwater_physical_aug_v1`, probability 0.75,
  with bounded channel attenuation, contrast/brightness changes, optional blur, artificial-light hotspot,
  particles, small occlusion, and optional JPEG degradation. Training default seed is 42.
- **Checkpoint format:** PyTorch `.pt` dictionary containing `state_dict`, `labels`, `task`, `model_version`, and
  metadata including config/data-manifest hashes. This describes the expected format; no such checkpoint exists.
- **Known limitations:** single-frame visual indicators cannot confirm cracks, corrosion, structural integrity,
  chemistry, ecology or field safety. No temporal/sonar fusion or validated calibration is present in Model 1.

No architecture claim above depends on Model 2/Twin 2 code. No inference is required beyond reading the named
implementation/config files.

## 4. Evaluation Readiness

**Can Model 1 be evaluated today?** No. The existing evaluator cannot pass its first data-read step, and both
visual classifiers lack checkpoints.

The intended command is:

```powershell
python scripts/evaluate_multidomain.py `
  --labels dataset/processed/labels.csv `
  --domain-checkpoint models/oceansense_domain_efficientnet_b0.pt `
  --condition-checkpoint models/oceansense_condition_efficientnet_b0.pt `
  --output outputs/evaluation_reports/multidomain_metrics.json
```

Observed on the audited commit: exit code `1`, `FileNotFoundError` for
`dataset/processed/labels.csv`. Required checkpoints and ImageFolder trees are also absent. The current Python
environment has `torch`, but not `torchvision` or `ultralytics`; `pyproject.toml` declares these under the
`vision` and `detection` optional dependencies.

The smallest evidence-recovery action is to locate and restore the original visual Model 1 checkpoint pair and
the exact license-approved labels/images/split manifest used with them. This is recovery, not retraining. If no
such external/project-owned package exists, a real baseline evaluation cannot be recovered from this repo.

## 5. Blocker List

1. **Visual checkpoint pair missing**
   - Missing evidence: domain and condition EfficientNet-B0 `.pt` files with provenance metadata.
   - Why blocking: the evaluator cannot produce a prediction without both classifiers.
   - Remediation: search team storage, prior machines/releases and handoff archives; verify hashes and payload
     labels/config before placing approved copies at the intended paths.
   - Owner: **user / unknown original model owner**.
2. **Approved labelled image snapshot missing**
   - Missing evidence: actual images plus `dataset/processed/labels.csv`; current approved manifest has 0 rows.
   - Why blocking: no ground truth exists for metric computation.
   - Remediation: recover the original provenance-complete snapshot and populate/approve per-asset manifest
     records; do not fabricate labels or download external data under this task.
   - Owner: **user / dataset research**.
3. **Immutable train/validation/test split missing**
   - Missing evidence: materialized split or manifest tied to the recovered checkpoint.
   - Why blocking: metrics are not reproducible and leakage cannot be ruled out.
   - Remediation: recover the original split; only if no original exists, create a minimal approved evaluation
     dataset under separate authorization, grouped by mission/video/site.
   - Owner: **software co-founder** after user/data approval.
4. **Genuine metrics and failure predictions missing**
   - Missing evidence: `multidomain_metrics.json`, checkpoint prediction export and reviewed failure rows.
   - Why blocking: fixture samples and telemetry/PPO results cannot support a visual Model 1 baseline claim.
   - Remediation: after blockers 1-3, run the existing evaluator and populate the failure index from held-out
     predictions without tuning on the test split.
   - Owner: **software co-founder**.
5. **Audit environment lacks visual optional dependencies**
   - Missing evidence: importable `torchvision`; `ultralytics` only if a detector is recovered and evaluated.
   - Why blocking: after data recovery, classifier construction would fail.
   - Remediation: install the repository-declared `.[vision]` dependency in a recorded environment; install
     `.[detection]` only when an approved detector/box dataset exists.
   - Owner: **software co-founder**.

## 6. Recommended Next Step

**Recover missing files.** This is preferred over creating a new dataset because the mission is to determine
whether the *existing* Model 1 can be evaluated without retraining. Ask the original model/data owner for one
immutable package containing both classifier checkpoints, the exact approved asset manifest, canonical labels,
split assignment, config/environment record and any prior report. Verify hashes before running validation.

If that package cannot be found, keep Model 1 blocked and separately authorize creation of a minimal approved
evaluation dataset; that later step would evaluate a recovered checkpoint but would not reconstruct its
original training provenance.

## 7. Commands Run

| Command / method | Result |
|---|---|
| Directory inventory of `src`, `models`, `checkpoints`, `weights`, `data`, `dataset(s)`, `config(s)`, `scripts`, `notebooks`, `docs`, `runs`, `outputs`, `artifacts`, `tests` | `checkpoints`, `weights`, `datasets`, `notebooks`, and `runs` absent; other areas inspected. |
| `rg --files` for Model 1 names, checkpoint extensions, labels, metrics, predictions, confusion and splits | Found implementation/config/schema/scripts; no visual checkpoint or canonical labels. |
| `rg -n -i` across source/config/scripts/docs/tests/data/artifacts | Distinguished visual Model 1 references from telemetry, PPO, fixtures and Model 2 references. |
| `git rev-list --objects --all` and `git log --all --full-history` for `.pt/.pth/.ckpt/.onnx`, labels and metrics | No historical visual Model 1 checkpoint or canonical labels; tracked ONNX files are navigation policies. |
| Recursive local artifact scan including ignored files | Found ML-Agents checkpoints under ignored `results/`; their run names/config/model card identify navigation, not visual Model 1. Dependency-package ONNX fixtures were excluded. |
| `Test-Path` on expected checkpoints, labels, boxes, ImageFolders and metrics output | All returned `False`. |
| Manifest inspection | `approved_assets.csv`, `raw_assets.csv`, and `rejected_assets.csv` contain headers only. |
| `python scripts/validate_image_dataset.py ...` | Exit `1`: canonical `labels.csv` missing. |
| `python scripts/evaluate_multidomain.py ...` | Exit `1`: canonical `labels.csv` missing before model loading. |
| Python dependency discovery | `torch=True`, `torchvision=False`, `ultralytics=False`. |

No training command was run, no implementation code was modified, no external dataset was downloaded, and no
Model 2 or Twin 2 work was performed.
