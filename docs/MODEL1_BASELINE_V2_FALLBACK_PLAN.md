# Model 1 Baseline v2 Fallback Plan

**Plan date:** 2026-08-25  
**Fallback identity:** `model1_baseline_v2`  
**Scope:** planning only; no training, dataset download, checkpoint creation, Model 2 work, or Twin 2 work

## 1. Executive Decision

`model1_baseline_v2` is the approved fallback identity for a newly trained visual Model 1 baseline. It is **not** a reconstruction, validation, continuation, or freeze of the missing original Model 1.

The fallback remains inactive until one of the activation conditions in Section 2 is formally recorded. Until then, the team should pursue the original checkpoint package and dataset permissions in parallel. This plan does not claim that approved data currently exists, that training has occurred, or that any model is frozen.

## 2. Activation Criteria

Activate this plan only if at least one of the following is documented:

1. The complete original Model 1 recovery package is not received by **2026-09-01 at 17:00 Europe/Istanbul**.
2. Either recovered checkpoint fails the Model 1 loading contract, checksum/provenance review, architecture/task/class-order validation, or is random, partial, renamed, or unrelated.
3. The original labels, immutable split, dataset manifest, evaluation configuration, metrics, or license/access evidence cannot be recovered well enough to validate the original run.

Activation requires a dated decision entry that links to `docs/MODEL1_CHECKPOINT_RECOVERY_DECISION.md`. The original Model 1 must remain **blocked / not frozen**. Activating this fallback authorizes preparation of a new evidence chain; it does not by itself authorize training.

## 3. Required Dataset Package

The fallback dataset package must exist under `data/model1_baseline_v2/` and contain:

- `manifest.csv`: one row per source asset with stable asset ID, source dataset, source URL/reference, owner, license, access/permission proof, permitted ML uses, download/acquisition date, original file hash, local relative path, real/synthetic flag, mission/video/site/source group, and approval status;
- `labels.csv`: one row per selected RGB image using the canonical domain and condition labels, stable sample ID, asset ID, relative image path, group identifiers, annotator/reviewer IDs, adjudication status, label provenance, visibility/source/origin metadata, and exclusion reason where applicable;
- `split.csv`: immutable sample-to-train/validation/test assignment with split version, grouping key, seed, and snapshot hash;
- a versioned RGB image snapshot referenced by hashes, without silently mutable paths;
- license/permission evidence for every source and an approval log for every included asset;
- `README.md`: dataset version, scope, acquisition and exclusion procedure, schema, directory layout, intended use, limitations, and maintainers;
- `checksums.sha256`: hashes for the manifest, labels, split, source evidence, and every image in the immutable snapshot;
- `SOURCES.md`: source citations, canonical dataset versions, access dates, and links/references to the corresponding rights evidence;
- annotation instructions, dual-review/adjudication records, duplicate/near-duplicate audit, and dataset validation report.

No image may enter training or evaluation solely because it is publicly reachable. Assets with uncertain rights, unverifiable provenance, unresolved labels, corrupted files, or group leakage must be excluded. Synthetic data must be marked explicitly and kept out of the primary held-out test set.

## 4. Dataset Candidate Priority

Use candidates in this exact priority order:

1. **SubPipe** — primary real underwater RGB candidate, subject to version, asset-level license, and label review. Its native labels do not automatically satisfy the nine-condition schema.
2. **InspectVQA** — useful inspection imagery if the owner confirms the intended non-commercial/competition use or supplies alternative permission.
3. **CleanCam** — useful mainly for camera/visibility robustness. Its synthetic portion and viewport fouling labels do not automatically become structural or biological labels.
4. **Claru** — use only if access terms, cost, redistribution, and model-training rights are explicitly acceptable.
5. **Structural Defects and WPI supplemental data** — non-underwater transfer support only after rights review; never a substitute for underwater held-out evidence.
6. **K-Pipelines** — synthetic-only support; never primary validation evidence and never counted toward real-image minimums.
7. **Dryad context metadata** — contextual/provenance support only unless the exact image assets and ML permissions are separately verified.

Institution-owned ROV captures or separately approved sources are required where these candidates cannot provide lawful, representative coverage—especially marine debris, ecological stress indicators, fish/habitat activity, and aquaculture infrastructure concerns.

## 5. Label Schema

The architecture remains two independent EfficientNet-B0 classifiers using the current canonical schema.

**Domain classes (6):** `structure`, `nature_ecology`, `contamination`, `fishing_aquaculture`, `general_underwater`, `unknown`.

**Condition classes (9):** `normal_or_no_visible_concern`, `possible_structural_concern`, `biofouling`, `marine_debris`, `poor_visibility`, `ecological_stress_indicator`, `fish_or_habitat_activity`, `aquaculture_infrastructure_concern`, `unknown`.

Labels describe visible indicators, not confirmed diagnoses. A source label may be mapped only after image-level review under the project annotation guide.

| Canonical condition | Candidate source signal | Mapping rule / rejection boundary |
|---|---|---|
| `normal_or_no_visible_concern` | InspectVQA normal/non-corroded; reviewed SubPipe frames | Accept only after full-frame review finds no visible concern; absence of a source annotation is not normal. |
| `possible_structural_concern` | InspectVQA corrosion; manually reviewed SubPipe pipeline concerns; eligible Claru/WPI/structural-defect imagery | Require a visible structural indicator. A pipeline object alone is not a concern label. |
| `biofouling` | InspectVQA fouling; eligible Claru biofouling | Require visible biological growth on the inspected asset. CleanCam viewport fouling is a camera condition and is not automatically mapped here. |
| `marine_debris` | Approved debris imagery or owned ROV captures | No priority source is presumed sufficient; require separately approved, image-level evidence. |
| `poor_visibility` | Real CleanCam turbid/degraded scenes; reviewed underwater sources | Distinguish water-column visibility from camera occlusion, blur, compression, and synthetic degradation. Synthetic images go only to robustness evaluation. |
| `ecological_stress_indicator` | Approved ecological monitoring imagery | Require a visible indicator under written annotation rules; do not infer ecosystem health from scene context alone. |
| `fish_or_habitat_activity` | Approved ecology/ROV imagery | Require visible fish or habitat activity; empty habitat scenes do not qualify. |
| `aquaculture_infrastructure_concern` | Approved aquaculture inspection imagery | Require a visible concern on aquaculture infrastructure. CleanCam camera condition does not map to this class. |
| `unknown` | Reviewed out-of-scope or visually indeterminate images | Use for genuinely indeterminate/out-of-schema evidence, not as a substitute for missing annotations or low reviewer effort. |

Domain labels must be assigned independently from condition labels. For example, an image may be domain `structure` with condition `biofouling`, or domain `general_underwater` with condition `poor_visibility`. Automatic domain inference from dataset name is prohibited.

## 6. Minimum Dataset Size

The absolute locked evaluation minimum is **30 real RGB images for each of the 9 condition classes: 270 real images total**. Synthetic images do not count toward this minimum and must be reported in a separate robustness evaluation.

Before training a full nine-condition fallback, the recommended minimum development target is:

- 100 real training images per condition class;
- 30 real validation images per condition class;
- 30 locked real test images per condition class;
- **160 real images per condition class, or 1,440 real images total** before additional domain balancing.

The same image set must also provide at least 100 train, 30 validation, and 30 test examples for each of the six domain classes. If domain floors are not met by the 1,440-image condition-balanced set, more approved real images are required. Each class should span at least three independent train groups, one validation group, and one test group; two or more independent sources per class are preferred.

These are planning floors, not evidence that the images exist. If any class lacks the required lawful, representative coverage, training remains blocked rather than silently reducing the schema.

## 7. Split Policy

Create the split once, audit it, and freeze it before training:

- split by `mission_or_video_id` and, where available, site/platform/source group—not individual frames;
- keep adjacent frames, bursts, crops of the same image, and perceptual near-duplicates in one split;
- use seed 42 for reproducibility, but treat grouping and leakage review as more important than the nominal seed;
- target the Section 6 class floors while preserving real-world group independence;
- keep the final test split hidden from model selection, threshold selection, augmentation tuning, and early stopping;
- record every sample assignment in `data/model1_baseline_v2/split.csv` and hash the file;
- never replace a test image after results are viewed without issuing a new dataset/split version and invalidating the previous comparison;
- report synthetic and real samples separately; synthetic samples may augment training only if predeclared and may never enter the primary real test metric.

The current `scripts/split_image_dataset.py` groups by mission/video and uses seed 42, but activation requires an additional audit for source/site leakage and near-duplicates before `split.csv` becomes immutable.

## 8. Training Plan

Train two separate classifiers without changing the current EfficientNet-B0 architecture:

| Item | Predeclared value |
|---|---|
| Initialization | Torchvision ImageNet pretrained weights |
| Input | RGB, 224-pixel EfficientNet-B0 default resize/crop and normalization |
| Train augmentation | `underwater_physical_aug_v1`, probability 0.75, train split only |
| Loss / balance | weighted cross-entropy using training-split class counts; do not combine with weighted sampler |
| Optimizer | AdamW, learning rate `3e-4`, weight decay `0.01` |
| Schedule | 3-epoch linear warm-up, then cosine annealing to `1e-6` |
| Batch size | 16 |
| Maximum epochs | 30 |
| Model selection | highest validation macro F1 |
| Early stopping | patience 5, minimum validation macro-F1 improvement 0.002; restore best checkpoint |
| Seed | 42 for Python, NumPy, PyTorch, sampler, and workers |
| Determinism | deterministic algorithms with warnings recorded; preserve environment/CUDA details |
| Hardware | one CUDA GPU with at least 8 GB preferred; CPU allowed but expected to be slow |
| Precision | full precision for the first reproducible baseline; mixed precision requires a separately recorded config |

Before a run, extend `scripts/train_classifier.py`/config handling so it can consume `configs/model1_baseline_v2.yaml`, save the explicit v2 identity, select on validation macro F1, implement the declared scheduler/early stopping, and record complete history/config/environment. This preparation is required because the current script hard-codes a v1 model version, selects on validation accuracy, and has no scheduler or early stopping. It does not authorize an architecture change.

Intended gated commands, documented but **not executed**:

```powershell
python scripts/train_classifier.py `
  --config configs/model1_baseline_v2.yaml `
  --task domain `
  --data data/model1_baseline_v2/imagefolders/domain `
  --output models/model1_baseline_v2_domain_efficientnet_b0.pt `
  --report reports/model1_baseline_v2_domain_training.json `
  --epochs 30 --batch-size 16 --seed 42 `
  --class-balance weighted_loss --weights imagenet `
  --data-manifest data/model1_baseline_v2/manifest.csv

python scripts/train_classifier.py `
  --config configs/model1_baseline_v2.yaml `
  --task condition `
  --data data/model1_baseline_v2/imagefolders/condition `
  --output models/model1_baseline_v2_condition_efficientnet_b0.pt `
  --report reports/model1_baseline_v2_condition_training.json `
  --epochs 30 --batch-size 16 --seed 42 `
  --class-balance weighted_loss --weights imagenet `
  --data-manifest data/model1_baseline_v2/manifest.csv
```

The commands become executable only after the config option and declared behavior are implemented, reviewed, and tested in a separate authorized preparation task.

## 9. Evaluation Plan

Evaluate the frozen candidate hashes once on the untouched real test split:

```powershell
python scripts/evaluate_multidomain.py `
  --labels data/model1_baseline_v2/labels.csv `
  --domain-checkpoint models/model1_baseline_v2_domain_efficientnet_b0.pt `
  --condition-checkpoint models/model1_baseline_v2_condition_efficientnet_b0.pt `
  --output reports/model1_baseline_v2_metrics.json
```

Before evaluation, extend the evaluator so it writes the complete prediction ledger, `reports/model1_baseline_v2_confusion_matrix.png`, and reviewed examples under `reports/model1_baseline_v2_failure_cases/`; the current evaluator retains only a 20-sample preview and does not produce the required PNG or latency record.

Required primary metrics:

- domain and condition accuracy;
- macro F1 and balanced accuracy for both heads;
- per-class precision, recall, F1, support, and confusion matrix;
- expected calibration error and predeclared confidence/abstention analysis;
- per-domain condition accuracy and breakdowns by source, visibility, mission/site, and real/synthetic origin;
- safety-relevant false negatives and high-confidence `unknown`/out-of-schema errors;
- batch-size-1 latency after warm-up, reporting p50/p95 on a named CPU and target GPU with software/hardware versions;
- checkpoint, manifest, labels, split, config, environment, and prediction-ledger hashes.

Failure review must export representative false positives, false negatives, low-confidence correct predictions, high-confidence wrong predictions, and class-confusion examples. It must specifically include false negatives for `possible_structural_concern`, `marine_debris`, `poor_visibility`, and `aquaculture_infrastructure_concern`; domain confusion; biofouling-versus-structural confusion; camera occlusion-versus-water visibility; synthetic-to-real failure; unknown/open-set behavior; duplicate/leakage suspects; and representative high-confidence errors. Synthetic robustness results must remain separate from the primary real-image metrics.

## 10. Freeze Criteria

Freeze is allowed only if every process gate passes and the numerical criteria were approved in `configs/model1_baseline_v2.yaml` before the test set was opened.

Process gates:

- all assets are approved and license/access proof is complete;
- all 6 domain and 9 condition classes meet the real-image floors;
- labels are dual-reviewed/adjudicated and all unresolved rows are excluded;
- manifest, labels, split, config, environment, and checkpoints are immutable and hashed;
- group and near-duplicate leakage audits pass with zero unresolved leakage;
- the locked test set was not used for tuning or model selection;
- complete metrics, predictions, confusion matrices, latency, and failure cases exist;
- a same-environment rerun reproduces prediction IDs/classes/confidences and hashes, or any unavoidable numeric tolerance is declared before rerun;
- limitations and claim boundaries explicitly reject diagnostic, safety-certification, and “perfect open-sea performance” claims.

Proposed engineering baseline thresholds to pre-register before activation:

- domain macro F1 and balanced accuracy at least 0.80, with every domain recall at least 0.60;
- condition macro F1 and balanced accuracy at least 0.70, with every condition recall at least 0.50;
- recall at least 0.75 for `possible_structural_concern`, `marine_debris`, and `poor_visibility`;
- expected calibration error no greater than 0.15;
- zero unresolved rights, adjudication, corruption, or leakage failures.

These thresholds qualify only a documented competition baseline. They do not prove flawless behavior, real-ocean generalization, autonomous safety, or field readiness. A failed threshold keeps the candidate **not frozen** and requires a new version/evidence cycle; the test set must not be repeatedly tuned against.

## 11. Artifact Naming

Canonical v2 artifacts are:

- `models/model1_baseline_v2_domain_efficientnet_b0.pt`
- `models/model1_baseline_v2_condition_efficientnet_b0.pt`
- `configs/model1_baseline_v2.yaml`
- `data/model1_baseline_v2/manifest.csv`
- `data/model1_baseline_v2/labels.csv`
- `data/model1_baseline_v2/split.csv`
- `reports/model1_baseline_v2_metrics.json`
- `reports/model1_baseline_v2_confusion_matrix.png`
- `reports/model1_baseline_v2_failure_cases/`

Training reports and the full prediction ledger may add unambiguous `model1_baseline_v2_*` filenames under `reports/`. Do not overwrite, rename, or backfill the missing original `models/oceansense_*_efficientnet_b0.pt` paths. Every v2 checkpoint payload must carry `model_version: model1_baseline_v2`, its task, ordered label list, config hash, data/split hashes, run ID, seed, and environment metadata.

## 12. Reproducibility

The evidence bundle must record:

- Git commit and clean/dirty state;
- complete `configs/model1_baseline_v2.yaml` and command lines;
- Python, operating system, Torch, Torchvision, CUDA/cuDNN, Pillow, NumPy, and GPU/CPU versions;
- seed 42 and deterministic-algorithm/warning status;
- exact package lock or environment export;
- SHA-256 for source assets, image snapshot, manifest, labels, split, config, checkpoints, metrics, confusion matrix, and prediction ledger;
- ordered class lists and preprocessing/augmentation versions;
- training history, best-epoch selection evidence, runtime, and hardware;
- immutable run ID and reviewer approvals.

Reproduction means using the same approved snapshot and config to obtain the recorded model-selection behavior and evaluation outputs within a predeclared tolerance. A new data snapshot, package version, seed, or config creates a new run/version rather than silently replacing evidence.

## 13. Audit

Create `docs/MODEL1_BASELINE_V2_FREEZE_AUDIT.md` only when a real candidate and complete evidence bundle exist. It must assess each dataset, rights, labeling, split, training, evaluation, reproducibility, failure-review, claim-boundary, and artifact requirement using exactly one status:

- **Fulfilled** — direct file/hash/report evidence exists and is cited;
- **Not fulfilled** — the requirement was attempted or evaluated and failed;
- **Blocked** — required input, permission, or authorized execution has not occurred.

The audit must end with one decision: `FROZEN`, `NOT FROZEN`, or `BLOCKED`. Planning documents, empty templates, sample predictions, or placeholder files cannot earn **Fulfilled**. This fallback plan itself does not create the audit and does not freeze Model 1.

## 14. Relationship to Model 2

`model1_baseline_v2` is still Model 1: a conventional EfficientNet-B0 visual perception baseline. It is not Model 2, is not proprietary structural intelligence, and does not replace future Model 2 research and development. It may provide baseline visual observations that later support Model 2 through a versioned interface containing class probabilities, confidence/abstention state, model hash/version, and timestamp/provenance. Model 2 remains a separate downstream decision/risk component with its own contracts and evidence.

No Model 2 retraining, recalibration, threshold change, claim change, or freeze is authorized by activating this plan. Until Model 1 v2 is frozen, any Model 2 use of its outputs must be marked experimental and must not be presented as end-to-end validated performance. Twin 2 is outside scope.

## 15. Recommended Next Action

**Proceed to dataset permission requests.**

Send the original checkpoint-package request immediately and retain the 2026-09-01 17:00 Europe/Istanbul deadline, while completing permission/rights requests in the priority order from Section 4. This parallel work is reusable whether the original package is recovered or the v2 fallback activates. Do not collect, download, label, split, or train assets until the relevant permissions and project authorization are recorded.

## Integrity Statement

No Model 1 training was performed. No external dataset was downloaded. No checkpoint, fake metric, fake label, placeholder artifact, or freeze audit was created. No existing Model 1 architecture was changed. No Model 2 or Twin 2 file was changed. This document defines a future gate and does not claim that the dataset, model, evaluation, or freeze evidence currently exists.
