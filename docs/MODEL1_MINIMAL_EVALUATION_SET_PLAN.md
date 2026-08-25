# Model 1 Minimal Approved Evaluation Set Plan

**Status:** planning and approval only

**Decision date:** 2026-08-25

**Scope:** Model 1 visual domain and condition classifiers only; no training, downloading, or Model 2/Twin 2 work

This document is an engineering and data-governance plan, not legal advice. A public page or download button is not, by itself, evidence that the assets may be reused.

## 1. Executive Recommendation

**BUILD NEW APPROVED EVALUATION SET.**

The repository contains the Model 1 schema, preprocessing configuration, evaluation code, and governance templates, but it contains no approved evaluation images and no populated `labels.csv`. The old evaluation package was not recovered. A new, real-image, provenance-preserving, test-only snapshot is therefore required.

The set should contain **at least 270 independently selected real RGB images: 30 for each of the nine condition classes**, while also satisfying a minimum of 30 images for each of the six domain classes within the same snapshot. These are overlapping constraints; the total must grow above 270 whenever the domain floors or source-diversity rules cannot be met. This is a minimum engineering baseline, not a statistical certification claim.

The most promising sources for immediate permission work are InspectVQA and SubPipe for real subsea structure imagery, CleanCam for visibility/camera-condition robustness, and Claru if acceptable commercial terms and a representative sample can be obtained. None of the eight candidates alone covers the complete Model 1 schema. Missing real-image coverage must come from separately approved sources or user/institution-owned ROV captures.

The evaluation remains blocked even after the dataset is assembled until the exact visual checkpoint pair is recovered. Creating replacement checkpoints would be training and would define a new model, not evaluate the previously claimed Model 1.

## 2. Existing Internal Data Review

| Data Source | Found? | Path / Evidence | Usable for Evaluation? | License/Ownership Status | Notes |
|---|---:|---|---:|---|---|
| Approved image assets | No | `dataset/manifests/approved_assets.csv` contains only its header | No | No approved asset records | Do not infer approval from `dataset/sources.yaml`; each asset must pass the manifest gate. |
| Canonical processed labels | No | `dataset/processed/labels.csv` is absent | No | Not applicable | `labels.example.csv` is a schema example and explicitly says no image is distributed. |
| User/institution-owned ROV captures | No files found | Source category is listed in `dataset/sources.yaml` | Not now; potentially yes | Institution permission, site/harbor authorization, and ownership evidence required | Preferred route for schema gaps if releases and provenance can be documented. |
| Dataset fixture/sample records | Yes | Test fixtures and schema examples under `tests/` and `dataset/processed/labels.example.csv` | No | Test-only/generated examples | They validate code paths, not model performance. |
| Model 1 class schema | Yes | `config/labels.yaml` | Yes, as schema | Repository-owned configuration | Six domain classes and nine condition classes. |
| Model 1 preprocessing/model config | Yes | `config/model_config.yaml`, `src/oceansense/perception.py` | Yes, as configuration | Repository-owned code/configuration | EfficientNet-B0, 224-pixel input. |
| Evaluation implementation | Yes | `scripts/evaluate_multidomain.py`, `src/oceansense/evaluation.py` | Yes, after data and checkpoints exist | Repository-owned code | Consumes only rows whose split is `test`. |
| Model 1 checkpoint pair | No | Required paths documented in README and evaluation command | No | Origin and approval evidence not recovered | Exact missing files are listed in Section 7. |
| Prior metrics/predictions/failure examples | No | Recovery reports and repository search | No | Not recovered | Must be regenerated only after all gates pass. |

**Internal-data conclusion:** there is no current internal dataset that can support a real Model 1 evaluation. User-owned data is a candidate source, not an approved dataset, until asset-level ownership and access evidence is recorded.

## 3. External Dataset Candidate Review

| Dataset | URL | Priority | Modality | Relevant Labels | License/Access Status | Usable Now? | Required Approval Step | Recommended Use |
|---|---|---|---|---|---|---:|---|---|
| InspectVQA | <https://huggingface.co/datasets/anonymousSubmissionVqa2026/InspectVQA> | High | Real subsea RGB, masks/VQA metadata | normal, weld seam, corrosion, fouling | Dataset card states CC BY-NC 4.0 **or another owner-approved license**; intended project/competition and later commercial reuse are ambiguous | No | Obtain written owner approval covering evaluation, competition/demo use, derivatives, outputs, storage/redistribution, and attribution; archive the approval | Primary candidate for `structure`, `possible_structural_concern`, `biofouling`, and normal structure examples after dual review |
| SubPipe | <https://zenodo.org/records/12666132> | High | Real RGB, side-scan sonar, navigation/sensor data, annotations | Pipeline objects/regions; not a direct nine-class condition taxonomy | Public record and downloadable archives found, but no sufficiently explicit reusable asset license was verified; record includes ownership/copyright language | No | Obtain explicit written reuse terms from the rights holder; confirm evaluation, derivative labels, publication, redistribution, and attribution | Use independent RGB frames for structure/domain robustness; keep sonar/navigation outside the current RGB evaluator |
| Structural Defects (Bonnín-Pascual / Ortiz) | <https://xiscobonnin.github.io/resources/> | Medium-high | RGB images and defect masks; not necessarily underwater | corrosion, cracks, coating breakdown | University resource/download page and citation found; explicit dataset reuse license not verified | No | Request written license/permission and verify whether every distributed image/mask is covered | Supplemental structural-defect transfer test only; report the non-underwater domain shift separately |
| WPI / ARL Corrosion | <https://arl.wpi.edu/corrosion_dataset/> | Medium | RGB corrosion imagery/ratings; laboratory/non-underwater | corrosion severity/rating | Access/download and citation information found; explicit dataset license not verified | No | Obtain written reuse terms, attribution requirements, and permission for derived labels/results | Supplemental corrosion sensitivity test; never present it as open-sea validation |
| K-Pipelines | <https://github.com/leoxthomas/K-Pipelines> | Medium | Synthetic RGB pipeline images | corroded, non-corroded | Repository carries GPL-3.0, but the license coverage/provenance of generated image assets still requires asset-level review | No for primary set | Confirm generated assets are covered, preserve prompts/provenance and attribution, and approve each file; mark every row `synthetic=true` | Optional, separately reported synthetic challenge set only; never count toward the 270 real-image minimum |
| CleanCam | <https://zenodo.org/records/18952474> | Medium | Real and synthetic underwater RGB | viewport fouling/cleanliness levels; visibility-like degradation | Zenodo record states CC BY 4.0 and identifies real/synthetic subsets; still requires repository reviewer approval and per-asset provenance | No until internal approval | Snapshot license evidence, retain exact attribution and record version, separate real from synthetic, hash assets, and approve manifest rows | Strongest legally clear candidate for camera fouling/visibility robustness; labels require manual mapping because viewport fouling is not structural biofouling |
| Dryad ship biofouling survey | <https://datadryad.org/dataset/doi:10.5061/dryad.hdr7sqvkb> | Low-medium | Tabular survey CSV | vessel/biofouling context | Dryad requires deposited files to be CC0, but this record distributes survey tables rather than evaluation images | No for image evaluation | Verify record/version/CC0 snapshot if used for contextual analysis; do not manufacture image rows | Context and sampling rationale only; reject from the visual evaluation snapshot |
| Claru Underwater Inspection | <https://claru.ai/datasets/underwater-inspection> | Inspect carefully | Commercial real underwater RGB video/frames with metadata and annotations | corrosion, biofouling, structural damage; quality indicators | Provider describes a sample-request/commercial delivery workflow; no public dataset license or unrestricted download was found | No | Request sample and contract; verify cost, source rights, exportability, storage, evaluation/training use, derived labels, result publication, redistribution, deletion, and attribution | Potential premium source for real structural classes if contract allows reproducible evaluation and evidence retention |

No candidate is marked usable now because the repository's own governance gate additionally requires an approved reviewer, asset URL, download timestamp, SHA-256, license URL, and attribution for every accepted asset. CleanCam has the clearest published reusable license, but it has not yet passed that internal per-asset gate.

## 4. Minimal Evaluation Set Definition

### 4.1 Coverage and counts

- **Condition target:** all nine classes in `config/labels.yaml`.
- **Minimum per condition class:** 30 real RGB images.
- **Minimum total:** 270 real RGB images.
- **Domain constraint:** at least 30 images for each of the six domain classes, satisfied within the same snapshot where possible. These counts overlap condition counts; add images when necessary.
- **Source/group constraint:** at least three independent `mission_or_video_id` groups per class and, wherever possible, at least two independent rights-cleared sources per class.
- **Frame independence:** no adjacent burst/video frames; use a documented temporal separation rule and perceptual-hash duplicate screening. Near-duplicates stay in one source group and only one representative enters the set.
- **Synthetic policy:** zero synthetic images in the primary 270. A synthetic challenge appendix may exist separately and must be reported separately.

The number 30 is a floor chosen to expose obvious class failures and permit per-class descriptive metrics. It is not sufficient to claim flawless open-sea performance, safety, or narrow confidence intervals.

### 4.2 Accepted modalities and annotations

- Accept JPEG or PNG **RGB still frames** readable by the current 224-pixel EfficientNet preprocessing path.
- Extracted video frames are acceptable only with source video ID and timestamp.
- Do not feed sonar, navigation telemetry, survey tables, masks, or video sequences directly into the current classifier. They may be retained as provenance or annotation aids.
- Use the existing CSV schema in `dataset/processed/labels.example.csv`; all accepted rows use `split=test`.
- `primary_label` must be one canonical condition class. `secondary_labels` may contain canonical co-occurring conditions separated by semicolons.
- `inspection_domain` must be one canonical domain class. Labels describe visual indicators, not confirmed engineering or ecological diagnoses.

### 4.3 Label creation and verification

1. A first reviewer assigns domain, primary/secondary condition, visibility, anomaly, risk, confidence, and notes from a written labeling guide.
2. A second reviewer independently verifies every row without seeing the first reviewer's confidence.
3. Disagreements are adjudicated by a named subsea-inspection or relevant ecology/aquaculture reviewer. The source's label may inform review but is never copied without mapping verification.
4. Record reviewer IDs, original source label, mapping rationale, and adjudication outcome in an annotation-audit sidecar.
5. Exclude ambiguous images unless they are intentionally and consistently labeled `unknown`. Low-confidence records do not enter a named-condition class.
6. Require 100% manifest/label agreement, 100% dual review, and zero unresolved adjudications before lock.

### 4.4 Required metadata and schemas

`labels.csv` must retain every field enforced by `src/oceansense/data.py`:

`sample_id,file_path,source,license,split,inspection_domain,primary_label,secondary_labels,contains_anomaly,condition_status,risk_level,weak_point_present,visibility_level,confidence_label,synthetic,mission_or_video_id,notes`

The approved-asset manifest must retain every field enforced by `src/oceansense/governance.py`:

`sample_id,source_name,source_url,original_asset_url,license,license_url,attribution,downloaded_at,sha256,inspection_domain,primary_label,annotation_type,mission_or_video_id,frame_timestamp,real_or_synthetic,approved_by,approval_status,notes`

The annotation-audit sidecar must add: `sample_id`, original source label, reviewer A, reviewer B, agreement state, adjudicator, adjudicated label, mapping version, and review timestamps.

### 4.5 Proof, naming, and immutable split

- Required proof: immutable license/terms snapshot or written permission; dataset version/DOI; asset-level source URL; attribution; named approval reviewer; approval timestamp; SHA-256.
- Filename: `M1E-{SOURCE}-{GROUP}-{FRAME}.{jpg|png}`, uppercase stable source code and zero-padded frame number. `sample_id` is the extension-free filename and never changes.
- Place approved images below `dataset/processed/model1_min_eval_v1/images/` or use a content-addressed read-only store referenced by the immutable manifest.
- This is an **external evaluation snapshot**, not a training corpus: `train=0`, `val=0`, `test>=270`. Do not use `stratified_split()` and do not tune thresholds on this set.
- Create `dataset/splits/model1_min_eval_v1_test.txt` containing sorted sample IDs, one per line.
- Freeze dataset version, source groups, mappings, configuration, checkpoint hashes, file hashes, and split-file hash in `dataset/manifests/model1_min_eval_v1_lock.json`.
- Any post-lock addition, relabel, or removal creates `v2`; it never silently changes `v1`.

## 5. Proposed Class Mapping

| Existing Model 1 Class | Candidate Dataset Label(s) | Mapping Confidence | Notes |
|---|---|---:|---|
| `normal_or_no_visible_concern` | InspectVQA `normal`; K-Pipelines `non-corroded`; lowest/none WPI rating after review | Medium | “No corrosion” is not the same as “no visible concern.” Require full-frame manual review. Synthetic K-Pipelines examples stay supplemental. |
| `possible_structural_concern` | InspectVQA `corrosion`; Structural Defects corrosion/crack/coating breakdown; WPI corrosion; K-Pipelines corroded; Claru corrosion/structural damage | High for direct real labels; medium/low otherwise | Canonical class is deliberately cautious: a visual indicator, not a structural diagnosis. |
| `biofouling` | InspectVQA `fouling`; Claru biofouling | High after visual verification | CleanCam viewport fouling is a camera obstruction and must not automatically map here. Dryad has no images. |
| `marine_debris` | None among the eight candidates | None | Obtain separately approved real underwater debris imagery or owned ROV captures. |
| `poor_visibility` | CleanCam degraded/fouled viewport levels, only after manual distinction from true water visibility | Medium | Record whether degradation is water-column turbidity, optical fouling, blur, or occlusion; mapping may require secondary labels/notes. |
| `ecological_stress_indicator` | None among the eight candidates | None | Requires separately approved ecology imagery and qualified visual-label review. |
| `fish_or_habitat_activity` | None among the eight candidates | None | Requires separately approved fish/habitat imagery; ordinary incidental fish require a consistent policy. |
| `aquaculture_infrastructure_concern` | None among the eight candidates | None | CleanCam camera condition is not cage/net damage. Obtain approved aquaculture inspection imagery. |
| `unknown` | Manually verified out-of-scope/indeterminate frames from approved sources | Medium | Do not create `unknown` merely because a source lacks a label. Use predefined inclusion rules and hard-negative review. |

The six domain classes must be assigned independently. Most structural candidates map to `structure`; CleanCam may map to `general_underwater` or `fishing_aquaculture` only when the visible context supports it. The remaining `nature_ecology`, `contamination`, `fishing_aquaculture`, `general_underwater`, and `unknown` domain coverage will likely require additional approved sources beyond the eight candidates.

## 6. Required Files Before Evaluation

The following files/artifacts must exist and be locked before `scripts/evaluate_multidomain.py` can run:

1. `dataset/processed/model1_min_eval_v1/images/` **or** an immutable content-addressed image manifest with locally resolvable files.
2. `dataset/processed/model1_min_eval_v1/labels.csv` with at least 270 valid `test` rows.
3. `dataset/splits/model1_min_eval_v1_test.txt` with the exact sorted test IDs.
4. `config/labels.yaml` and its recorded SHA-256.
5. `config/model_config.yaml` plus the preprocessing implementation/version and hashes.
6. `models/oceansense_domain_efficientnet_b0.pt`.
7. `models/oceansense_condition_efficientnet_b0.pt`.
8. `config/model1_min_eval_v1.yaml` recording paths, versions, seed/non-random selection policy, reporting outputs, and checkpoint hashes.
9. `dataset/manifests/model1_min_eval_v1_approved_assets.csv` with only approved rows.
10. `dataset/manifests/model1_min_eval_v1_license_evidence/` containing terms snapshots or written approvals and attribution text.
11. `dataset/processed/model1_min_eval_v1/ANNOTATION_AUDIT.csv` with dual-review/adjudication evidence.
12. `dataset/processed/model1_min_eval_v1/README.md` describing scope, sources, mappings, limitations, exclusions, class/domain counts, and versioning.
13. `dataset/manifests/model1_min_eval_v1_checksums.sha256` covering images and material metadata/config files.
14. `dataset/manifests/model1_min_eval_v1_lock.json` pinning manifest, split, schema, config, and checkpoint hashes.

After evaluation, but not as part of this planning task, preserve the full predictions, aggregate/per-class/per-domain/per-source metrics, calibration results, false negatives, and representative failure examples. The current script's 20-row `sample_predictions` preview is not a complete prediction ledger and should be supplemented before freeze.

## 7. Checkpoint Dependency

**No. Evaluation cannot proceed without the missing visual checkpoint pair.**

Required exact files:

- `models/oceansense_domain_efficientnet_b0.pt`
- `models/oceansense_condition_efficientnet_b0.pt`

`scripts/evaluate_multidomain.py` requires both command-line arguments and constructs both classifiers from those files. The adapters in `src/oceansense/perception.py` also validate checkpoint task/label compatibility. Random ImageNet initialization, a newly trained model, a renamed file, or one half of the pair would not reproduce evaluation of the missing Model 1 claim.

Before acceptance, verify SHA-256, architecture/task metadata, class order, preprocessing compatibility, provenance, and that each file loads without modification. If the original pair cannot be recovered, Model 1 remains blocked and a separately authorized task must define and train a new model version.

## 8. Approval / Legal Gate

| Candidate | License Found? | Non-commercial Use Allowed? | Redistribution Allowed? | Download Permitted? | Attribution Required? | Separate Owner Approval Required? |
|---|---|---|---|---|---|---|
| InspectVQA | CC BY-NC 4.0 or owner-approved alternative stated | Appears yes under CC BY-NC, but project scope must be confirmed | Conditional under license; project redistribution scope unresolved | Page exposes dataset access | Yes | **Yes for this project** to remove competition/commercial/derivative ambiguity |
| SubPipe | No sufficiently explicit reusable asset license verified | Unknown | Unknown | Archives are publicly downloadable | Ownership/citation text should be preserved | **Yes** |
| Structural Defects | No explicit dataset license verified | Unknown | Unknown | Resource archives are linked | Citation is requested | **Yes** |
| WPI / ARL Corrosion | No explicit dataset license verified | Unknown | Unknown | Access/download instructions are shown | Citation appears expected | **Yes** |
| K-Pipelines | GPL-3.0 repository license found; image-asset coverage needs confirmation | Likely for covered works, but do not assume asset coverage | Conditional on GPL obligations if images are covered | Repository download is available | Yes/license notices required | Reviewer/author clarification required before accepting generated images |
| CleanCam | CC BY 4.0 on versioned Zenodo record | Yes | Yes under CC BY terms | Yes | Yes | No separate owner permission indicated by the published license, but **internal asset approval is still required** |
| Dryad biofouling survey | Dryad requires deposited files to be CC0 | Yes | Yes for deposited tables | Yes | CC0 does not legally require attribution; scholarly citation is still appropriate | No for the tables, subject to version/license snapshot; unusable as image data |
| Claru | No public dataset license found | Contract-dependent | Contract-dependent | Sample request, not unrestricted public download | Contract-dependent | **Yes; signed terms/order required** |

Approval is granted only when a named reviewer sets `approval_status=approved` and all evidence required by `src/oceansense/governance.py` is present. Unknown, custom, non-commercial, or contract licenses require manual review. If redistribution is prohibited, the repository may store only hashes/manifests and reproducible access instructions; the evaluator still needs authorized local copies.

## 9. Next Decision Gate

**Next action: recover checkpoint package.**

Dataset permission requests for InspectVQA, SubPipe, Structural Defects, WPI, and Claru and the internal CleanCam license snapshot can proceed in parallel, but the next go/no-go decision is whether the exact checkpoint pair can be recovered and authenticated. Without it, a completed evaluation set cannot evaluate the previously claimed Model 1. If recovery fails, keep Model 1 blocked and request explicit authorization to define a new model version; do not silently retrain under the old identity.

Once both checkpoints pass provenance and load checks, the ordered data gates are: request/record permissions -> download only approved assets -> dual-label and adjudicate -> create and hash the immutable test snapshot -> run evaluation -> review failures -> decide whether Model 1 can be frozen.

## 10. Commands / Sources Reviewed

### Repository commands

- `Get-Content` on the Step 3 request, `config/labels.yaml`, `config/model_config.yaml`, `dataset/processed/labels.example.csv`, `dataset/manifests/approved_assets.csv`, `dataset/sources.yaml`, `src/oceansense/data.py`, `src/oceansense/governance.py`, and `scripts/evaluate_multidomain.py`.
- `rg --files docs` to inventory existing documentation.
- `rg -n "checkpoint|models/.*\\.pt|condition_efficient|domain_efficient" ...` to confirm the checkpoint interface and expected paths.
- `git status --short` and `git log -5 --oneline --decorate` to establish repository state and prior recovery work.

### Official dataset/source pages

- InspectVQA dataset card: <https://huggingface.co/datasets/anonymousSubmissionVqa2026/InspectVQA>
- SubPipe Zenodo record: <https://zenodo.org/records/12666132>
- Structural Defects resources: <https://xiscobonnin.github.io/resources/>
- WPI/ARL Corrosion Dataset: <https://arl.wpi.edu/corrosion_dataset/>
- K-Pipelines repository and GPL-3.0 license: <https://github.com/leoxthomas/K-Pipelines>
- CleanCam Zenodo record: <https://zenodo.org/records/18952474>
- Dryad biofouling record: <https://datadryad.org/dataset/doi:10.5061/dryad.hdr7sqvkb>
- Dryad good data practices/CC0 requirement: <https://datadryad.org/help/guides/best_practices>
- Claru Underwater Inspection Dataset: <https://claru.ai/datasets/underwater-inspection>

No external dataset was downloaded, no labels were fabricated, no training was run, and no Model 1 architecture or Model 2/Twin 2 file was changed while producing this plan.
