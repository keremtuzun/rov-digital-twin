# Model 1 Dataset Permission and Access Request Package

**Prepared:** 2026-08-25

**Status:** ready for human review and sending; no request has been sent by the repository agent

**Scope:** Model 1 approved dataset acquisition only. This package does not authorize downloading, training, or accepting data.

## 1. Immediate Routing Decision

| Candidate | Priority | Published status | External message needed now? | Immediate action | Current gate |
|---|---:|---|---:|---|---|
| SubPipe | 1 | Official Zenodo API metadata identifies record `12666132`, version 3.0.1, as open under CC BY 4.0 | Optional clarification only | Archive the record/API metadata and license text, confirm every intended file is covered, plan attribution, then run internal per-asset approval | `LICENSE_SNAPSHOT_REQUIRED` |
| InspectVQA | 2 | Dataset card says CC BY-NC 4.0 or another owner-approved license | **Yes** | Ask the data owner for explicit project-specific written permission and identity/provenance clarification | `OWNER_PERMISSION_REQUIRED` |
| CleanCam | 3 | Official Zenodo API metadata identifies record `18952474`, version v1.0.0, as open under CC BY 4.0 | Optional clarification only | Resolve the “newer version” notice, snapshot the selected version/license, separate real/synthetic assets, and run internal per-asset approval | `VERSION_AND_LICENSE_SNAPSHOT_REQUIRED` |
| Claru | 4, conditional | Commercial sample-request/provider workflow; no public reusable dataset license found | **Yes, only after budget/terms pre-screen** | Request a small representative sample, price, and written rights matrix through the dataset page's “Request a Sample Pack / Get in Touch” route | `COMMERCIAL_TERMS_REQUIRED` |

Public availability does not equal repository approval. Even CC BY 4.0 assets must have versioned source evidence, exact attribution, original asset URL, license URL, download timestamp, SHA-256, named reviewer, and `approval_status=approved` before use.

## 2. Common Project Description for Requests

Use the following description consistently:

> OceanSense is a Conrad Challenge student project developing a research prototype for underwater inspection decision support. Model 1 uses RGB still images to classify inspection domain and visible-condition indicators. We are preparing a provenance-preserving dataset for a new baseline and an independently locked evaluation set. The system is not a certified inspection tool and will not claim physical integrity or safety from image classification alone.

Do not promise that the project is permanently non-commercial. Ask for terms that explicitly cover the current competition/research use and state what would be required for any later commercial or public deployment.

## 3. Rights and Access Questions Required in Every Response

Obtain written answers or an authoritative license record for:

1. Does the license cover the image/video files themselves, not only code or metadata?
2. Are Model 1 training and held-out evaluation allowed?
3. Is Conrad Challenge competition, judging, demo, pitch, and publication use allowed?
4. Are frame extraction, resizing, preprocessing, derived annotations, and class remapping allowed?
5. May trained checkpoint files, aggregate metrics, complete predictions, and failure examples be published?
6. May raw or derived images be stored in a private team repository? May any be redistributed publicly?
7. What exact attribution and citation text is required?
8. Are there non-commercial, geographic, export, institutional, time, user-count, or deletion restrictions?
9. Does the provider warrant or document that it has the necessary rights from image/site/data owners?
10. What dataset version, DOI, file list, split, checksums, and annotation guide define the granted package?

An unclear answer is not approval. Record it as `manual_review` and keep assets outside the approved manifest.

## 4. Ready-to-Send InspectVQA Request

**Route:** Hugging Face dataset Community/Discussion for `anonymousSubmissionVqa2026/InspectVQA`, followed by a private owner channel if supplied.

**Subject:** Permission and provenance request — InspectVQA use in OceanSense Conrad Challenge project

> Hello,
>
> We are preparing the OceanSense Model 1 visual baseline for a Conrad Challenge student project focused on underwater inspection decision support. We would like to use a rights-cleared subset of InspectVQA for RGB training and independently held-out evaluation, especially the normal, weld seam, corrosion, and fouling labels.
>
> The dataset card states “CC BY-NC 4.0, or another license approved by the data owner.” Before accessing the data, could the data owner please confirm in writing whether our use is permitted for:
>
> - Conrad Challenge research, judging, demonstrations, pitch materials, and publication;
> - training and held-out evaluation of EfficientNet-B0 classifiers;
> - frame preprocessing, derived annotations, label mapping, and failure analysis;
> - private team storage of approved assets;
> - publication of trained checkpoints, aggregate/per-class metrics, predictions, and limited attributed failure examples;
> - any later commercial use, or the separate license that would be required for it?
>
> Please also identify the data owner/licensor, confirm that the license covers the underlying images and annotations, provide the required attribution/citation text, and state any redistribution, deletion, geography, export, or user-access restrictions. If approval is granted, please identify the exact dataset version/file manifest covered by the permission.
>
> We will not download or use the dataset until the permission and provenance evidence passes our internal review. Thank you.

**Accept only if:** the respondent's authority is identifiable and the response explicitly covers images, annotations, intended uses, derivatives, outputs, attribution, and restrictions. A reply from an anonymous account without licensor authority remains insufficient.

## 5. SubPipe Internal Approval and Optional Clarification

**Authoritative record:** <https://zenodo.org/records/12666132>  
**Metadata endpoint reviewed:** <https://zenodo.org/api/records/12666132>  
**Observed metadata:** version 3.0.1, open access, CC BY 4.0, DOI `10.5281/zenodo.12666132`.

CC BY 4.0 does not normally require separate owner permission, but the repository still needs an internal evidence package. Before any download:

- save a dated human-readable record snapshot and API metadata snapshot;
- save the canonical CC BY 4.0 license text/URL;
- record creators, DOI, version, citation, file list, and intended attribution;
- verify the license applies to each intended RGB/annotation file and note any third-party exceptions;
- predeclare whether extracted video frames may be redistributed or only stored privately;
- after authorized download, calculate SHA-256 per accepted asset and complete reviewer approval.

**Optional clarification subject:** SubPipe 3.0.1 — confirmation of CC BY 4.0 coverage for extracted RGB frames and derived labels

> Hello,
>
> We are evaluating SubPipe 3.0.1 for the OceanSense Conrad Challenge student project. Zenodo API metadata for DOI 10.5281/zenodo.12666132 identifies the record as open under CC BY 4.0. Could you please confirm that CC BY 4.0 covers all RGB/video and annotation files in the release, including extracted still frames and derived class mappings? Please also confirm the preferred attribution/citation and identify any third-party files or site imagery that carry different restrictions.
>
> We plan to keep sonar/navigation modalities separate from the current RGB classifier and will preserve version, source, attribution, and file hashes.

The optional note must not be described as legally required permission unless internal review identifies a real ambiguity.

## 6. CleanCam Internal Approval and Optional Version Clarification

**Authoritative record:** <https://zenodo.org/records/18952474>  
**Metadata endpoint reviewed:** <https://zenodo.org/api/records/18952474>  
**Observed metadata:** version v1.0.0, open access, CC BY 4.0, DOI `10.5281/zenodo.18952474`; the record page reports that a newer version exists.

Before any download:

- resolve and select the exact frozen version; do not silently mix versions;
- snapshot the selected record/API metadata and CC BY 4.0 evidence;
- preserve creator attribution, DOI, version, official capture-disjoint split, file list, and checksums;
- separate 18,972 reported real images from 3,600 reported synthetic images;
- treat viewport fouling as camera-condition/visibility robustness unless a reviewer justifies a canonical Model 1 label mapping;
- do not count synthetic images toward the primary real-image evaluation minimum;
- pass all selected assets through internal per-asset approval.

**Optional clarification subject:** CleanCam version and recommended use for external camera-condition evaluation

> Hello,
>
> We are preparing an approved visual evaluation set for the OceanSense Conrad Challenge student project. We are considering CleanCam for camera-fouling and visibility-robustness evaluation, not as direct structural-defect ground truth.
>
> Could you identify the current recommended frozen release, confirm that the Zenodo CC BY 4.0 license covers the real and synthetic image files plus metadata, and provide the preferred citation/attribution? Please also confirm whether the official capture-disjoint split should be preserved when selecting a small independent evaluation subset and whether there are any restrictions beyond CC BY 4.0.

## 7. Ready-to-Send Claru Commercial Inquiry

**Route:** “Request a Sample Pack / Get in Touch” on <https://claru.ai/datasets/underwater-inspection>. Do not use a footage-seller/partnership intake as the buyer route.

**Subject:** Student evaluation sample and licensing terms — Claru Underwater Inspection Dataset

> Hello,
>
> We are the OceanSense Conrad Challenge student team, preparing a provenance-preserving RGB dataset for an underwater inspection decision-support baseline. Your Underwater Inspection Dataset appears relevant for corrosion, biofouling, structural-damage indicators, and degraded visual conditions.
>
> Before considering purchase, could you provide a small representative sample with its annotation guide and a written proposal covering:
>
> - sample/package size, sites, sensors, environments, class counts, and independent sequence/site splits;
> - total and student/non-profit pricing, minimum order, delivery format, and lead time;
> - rights for Model 1 training and held-out evaluation, Conrad judging/demo/pitch/publication, derived annotations, and class remapping;
> - whether trained checkpoints, aggregate/per-class metrics, complete prediction logs, and limited failure examples may be published;
> - storage, user-count, geography/export, security, deletion, term, and audit requirements;
> - whether raw frames may be redistributed or whether only manifests/hashes and aggregate results may be published;
> - data provenance, site/subject permissions, annotation quality controls, and required attribution.
>
> We will not ingest the sample into training or evaluation until the contract and asset provenance pass internal review. If the terms cannot support reproducible competition evaluation and evidence retention, please state that clearly so we can close the candidate.

**Proceed only if:** price and lead time are realistic; the agreement permits the required competition/evaluation uses; the team can retain enough evidence for reproducibility; and prohibited redistribution can be handled with private authorized storage plus public hashes/manifests. Otherwise mark `REJECTED_COMMERCIAL_TERMS`.

## 8. Request Tracker

| Candidate | Owner/route | Package status | Send status | Response deadline | Approval decision |
|---|---|---|---|---|---|
| SubPipe | Zenodo record/creators | Internal evidence checklist ready; optional clarification ready | `NOT_SENT` | Set by human sender | `PENDING_INTERNAL_REVIEW` |
| InspectVQA | Hugging Face Community/owner | Permission request ready | `NOT_SENT` | Set by human sender | `OWNER_PERMISSION_REQUIRED` |
| CleanCam | Zenodo record/creators | Internal evidence checklist and optional version note ready | `NOT_SENT` | Set by human sender | `PENDING_VERSION_REVIEW` |
| Claru | Dataset sample/contact route | Commercial inquiry ready | `NOT_SENT` | Set by human sender | `COMMERCIAL_TERMS_REQUIRED` |

For every sent message, record sender, recipient/route, UTC timestamp, exact message hash/copy, response deadline, response file, reviewer, and final decision. Do not put an asset into `dataset/manifests/approved_assets.csv` merely because a request was sent.

## 9. Required Evidence Files After Responses

Store evidence under a future, reviewer-approved structure such as:

```text
dataset/licenses/model1_candidates/
  inspectvqa/
    request.txt
    response.txt
    owner_identity_and_authority.md
    license_or_permission.txt
  subpipe-3.0.1/
    zenodo_record_snapshot.html
    zenodo_api_metadata.json
    cc-by-4.0.txt
    attribution.txt
  cleancam-vX/
    zenodo_record_snapshot.html
    zenodo_api_metadata.json
    cc-by-4.0.txt
    attribution.txt
  claru/
    inquiry.txt
    sample_terms.pdf
    contract_or_rejection.md
```

Do not create fake responses, authority records, licenses, or approvals. Filenames above define the evidence target only.

## 10. Parallel Checkpoint Owner Message

Send separately to whoever performed the original Model 1 training:

> Do you have these two files: `oceansense_domain_efficientnet_b0.pt` and `oceansense_condition_efficientnet_b0.pt`, plus the exact approved image manifest, `labels.csv`, immutable train/validation/test split, evaluation config and commands, metrics, complete predictions/failure examples, license/access proof, environment record, and SHA-256 hashes? Please send the original files without renaming or re-saving them and identify the machine/run/date they came from.

The recovery deadline remains 2026-09-01 at 17:00 Europe/Istanbul. If the complete package is not received and validated, original Model 1 remains blocked/not frozen and any later training must use the separately authorized `model1_baseline_v2` identity.
