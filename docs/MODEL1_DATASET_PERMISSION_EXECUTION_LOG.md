# Model 1 Dataset Permission Request Execution Log

**Log opened:** 2026-08-25  
**Project:** OceanSense — Conrad Challenge  
**Scope:** Model 1 dataset permission and access tracking only  
**Checkpoint recovery deadline:** 2026-09-01 17:00 Europe/Istanbul

## 1. Executive Status

**REQUESTS PREPARED — LICENSE CLARIFICATION REQUIRED**

Exact requests are prepared below, but the repository contains no sent-message receipt, email/thread URL, provider response, signed terms, or completed internal approval record. Therefore no request is recorded as sent and no dataset is currently approved for Model 1 training or primary evaluation.

The official SubPipe `3.0.1` and current CleanCam `v2.0.0` API metadata were rechecked on 2026-08-26. Both responses exposed `metadata.rights=null`, so earlier repository statements that these specific records were CC BY 4.0 are not accepted as evidence. Metadata summaries are now archived locally, but both sources require authorized written license/file-scope clarification and internal approval before use. Dryad is usable only as CC0 tabular context after its metadata is archived; it is not visual Model 1 data. K-Pipelines is synthetic and cannot count toward primary evaluation. All other tracks require explicit owner/provider clarification.

For every future send or response, append the sender, recipient/route, UTC timestamp, exact message copy and SHA-256, thread/message URL or receipt, response deadline, response evidence path, reviewer, and decision. A prepared or sent request is never equivalent to approval.

## 2. Dataset Permission Tracker

| Dataset | URL | Owner/Contact | Request Needed? | Request Status | License Status | Approval Evidence | Usable for Primary Evaluation? | Usable for Supplemental Testing? | Next Action |
|---|---|---|---:|---|---|---|---:|---:|---|
| SubPipe | <https://zenodo.org/records/12666132> | Zenodo record creators/maintainers | Yes | `READY_FOR_HUMAN_SEND` | v3.0.1 confirmed; API license/rights field is null; public/citation wording is not a license grant | Metadata review at `data/model1_baseline_v2/licenses/subpipe/README.md`; no approval | No | No | Send written license/file-scope clarification to an authorized owner/licensor |
| InspectVQA | <https://huggingface.co/datasets/anonymousSubmissionVqa2026/InspectVQA> | Hugging Face Community for `anonymousSubmissionVqa2026`, then identified licensor | Yes | `PREPARED_NOT_SENT` | Dataset card states CC BY-NC 4.0 or owner-approved alternative; licensor authority and competition/output rights unresolved | None | No | No | Post the request in the dataset Community area; obtain an identifiable owner response covering images, annotations, derivatives, outputs, and restrictions |
| CleanCam | <https://zenodo.org/records/21515620> | Zenodo record creators/maintainers | Yes | `READY_FOR_HUMAN_SEND` | Current v2.0.0 confirmed; API license/rights field is null; v1.0.0 is superseded | Metadata review at `data/model1_baseline_v2/licenses/cleancam/README.md`; no approval | No; not a structural-defect primary source | No | Send written version/license/file-scope clarification; preserve real/synthetic separation |
| Claru Underwater Inspection | <https://claru.ai/datasets/underwater-inspection> | Claru “Request a Sample Pack / Get in Touch” route | Yes | `PREPARED_NOT_SENT` | Commercial/provider terms; no public reusable dataset license recorded | None | No | No | Submit inquiry only after budget/contract pre-screen; require written rights matrix, price, provenance, sample terms, and reproducibility allowances |
| Structural Defects — Bonnín-Pascual / Ortiz | <https://xiscobonnin.github.io/resources/> | Francisco Bonnín Pascual, University of the Balearic Islands; contact listed on resource page | Yes | `PREPARED_NOT_SENT` | Download and citation are published; explicit image/mask reuse license not recorded | None | No; non-underwater supplemental source only | No | Send written permission/license request covering images, masks, ML use, derivatives, checkpoints, examples, and attribution |
| WPI / ARL Corrosion | <https://arl.wpi.edu/corrosion_dataset/> | WPI Automation and Robotics Lab dataset maintainer/contact channel | Yes | `PREPARED_NOT_SENT` | Access/citation information reported; explicit dataset license and output rights unresolved | None | No; laboratory/non-underwater supplemental source only | No | Identify the authorized maintainer and send the prepared request; archive explicit terms and covered version/file list |
| K-Pipelines | <https://github.com/leoxthomas/K-Pipelines> | Repository maintainer via GitHub issue/contact | Yes, for image-asset provenance/coverage | `PREPARED_NOT_SENT` | Repository license reported as GPL-3.0; generated-image ownership, source rights, and license coverage unresolved | None | No; synthetic prohibited from primary set | No | Ask maintainer to confirm generated-image provenance/license and output obligations; approve only as a separately reported synthetic challenge set |
| Dryad Biofouling Survey Data | <https://datadryad.org/dataset/doi:10.5061/dryad.hdr7sqvkb> | Dataset authors / Dryad record; contact only if metadata ambiguity arises | No owner request currently required for deposited tables | `INTERNAL_EVIDENCE_NOT_ARCHIVED` | Existing review reports CC0 tabular survey data; no distributed evaluation images | None in approved local evidence structure | No; tabular-only | No for visual testing; context only after evidence archive | Archive DOI/version/CC0/citation metadata; record `CONTEXT_ONLY`; do not create image rows or Model 1 metrics from the tables |

“Usable” in this tracker means admitted through the repository governance gate, not merely visible online. At log creation, **zero datasets are usable for primary evaluation and zero are usable for visual supplemental testing**.

## 3. Request Messages

### 3.1 SubPipe — optional file-scope clarification

**Route:** Authorized Zenodo record creator/owner contact. This clarification is required.
**Subject:** SubPipe 3.0.1 license scope clarification — OceanSense Conrad Challenge

> Hello,
>
> We are the OceanSense student team participating in the Conrad Challenge. We are preparing a non-commercial research/competition RGB perception baseline for underwater inspection decision support and are considering a rights-cleared subset of SubPipe 3.0.1 for training and independently held-out evaluation.
>
> We would request only the release's RGB/video files, relevant annotations, file/version manifest, checksums, annotation guide, and citation metadata; sonar and navigation data would remain outside this visual classifier. We do not plan to redistribute raw source media publicly. We may need to store approved files privately, extract still frames, resize/preprocess them, create derived labels, publish trained checkpoints, aggregate/per-class metrics, complete prediction logs, and a limited number of attributed failure examples.
>
> The current public record and API metadata we reviewed do not expose a specific license grant. Could an authorized owner/licensor explicitly identify the applicable license and confirm in writing that it covers every intended RGB/video and annotation file, extracted still frames and derived labels, and identify any third-party or site imagery exceptions? Please also confirm whether trained checkpoints and the described research outputs may be published, the exact required attribution/citation, any redistribution or storage limits, and the exact version/file list covered.
>
> We will preserve the DOI, version, attribution, license URL, source URLs, and hashes. We will not use files whose coverage remains unclear. Thank you.

### 3.2 InspectVQA — permission and licensor identity

**Route:** Hugging Face dataset Community, followed by a private authorized-owner channel if supplied.  
**Subject:** Written permission and provenance request — InspectVQA for OceanSense Conrad Challenge

> Hello,
>
> We are the OceanSense student team participating in the Conrad Challenge, developing a non-commercial research/competition prototype for underwater inspection decision support. We would like to use a rights-cleared subset of InspectVQA RGB images, masks where relevant, labels/annotations, file manifest, split/provenance metadata, annotation guide, and citation information for EfficientNet-B0 training and independently held-out evaluation.
>
> We do not intend to redistribute the raw dataset publicly. Approved files would be stored in a private team workspace. We may resize/preprocess images, create derived class mappings, and publish trained checkpoints, aggregate and per-class metrics, complete prediction logs, and a small set of attributed failure examples.
>
> The dataset card states “CC BY-NC 4.0, or another license approved by the data owner.” Could an identifiable owner/licensor with authority explicitly confirm in writing that Conrad Challenge research, judging, demonstrations, pitch materials, and publication are permitted? Please clarify whether the license covers the underlying images, masks, annotations, derived labels, checkpoint publication, and the outputs described above; whether any raw/derived image redistribution is permitted; and whether later commercial use would require a separate license.
>
> Please provide the exact covered dataset version/file manifest, owner/licensor identity, required citation and attribution, and all storage, access, deletion, geographic, export, time, and user-count restrictions. We will preserve all required attribution and will not use the dataset until written permission and provenance pass internal review. Thank you.

### 3.3 CleanCam — optional release/version clarification

**Route:** Authorized Zenodo record creator/owner contact. This clarification is required.
**Subject:** CleanCam release and license clarification — OceanSense Conrad Challenge robustness study

> Hello,
>
> We are the OceanSense Conrad Challenge student team. For non-commercial research/competition use, we are considering CleanCam only as a separate underwater camera-fouling, visibility, and optical-degradation robustness set—not as primary structural-defect ground truth.
>
> We would request the selected release's real RGB images, separately identified synthetic images, metadata, official capture-disjoint split, annotation guide, file manifest/checksums, and citation information. We do not plan to redistribute raw source images publicly. We may store approved assets privately, resize/preprocess them, create reviewed derived mappings, and publish trained checkpoints, aggregate/per-class robustness metrics, prediction logs, and limited attributed failure examples.
>
> We found current release v2.0.0 at DOI 10.5281/zenodo.21515620, but the public API metadata we reviewed does not expose a specific license grant. Could an authorized owner/licensor confirm the recommended immutable release, identify the applicable license, and confirm that it covers both the identified real and synthetic image files plus metadata/annotations? Please state whether the described derivatives and checkpoint/results publication are allowed, whether any raw/derived redistribution or storage limits apply, and the exact required citation/attribution. Please also identify any third-party exceptions and whether the official capture-disjoint split must be retained for subset evaluation.
>
> We will keep real and synthetic results separate, preserve citation/license/version evidence, and will not use unresolved files. Thank you.

### 3.4 Claru — commercial terms and sample inquiry

**Route:** “Request a Sample Pack / Get in Touch” on the dataset page.  
**Subject:** Student sample and licensing proposal — Claru Underwater Inspection Dataset

> Hello,
>
> We are the OceanSense Conrad Challenge student team, developing a non-commercial research/competition RGB baseline for underwater inspection decision support. We are considering a representative Claru underwater-inspection subset if its provenance, price, delivery schedule, and contractual rights support reproducible student evaluation.
>
> Please provide a small review sample plus a proposed package description covering RGB clips/frames, annotations, file manifest/checksums, site/sequence grouping, sensor/environment metadata, annotation guide, class counts, and independent splits. We do not plan to redistribute raw media publicly; approved assets would be stored in an access-controlled private workspace.
>
> Please provide explicit written terms for training and held-out evaluation; Conrad judging, demo, pitch, and publication; frame extraction, preprocessing, derived labels and class remapping; publication of trained checkpoints, aggregate/per-class metrics, prediction logs, and limited attributed failure examples. Please separately state whether raw or derived images may be redistributed and whether public hashes/manifests are permitted.
>
> We also need total/student pricing, lead time, licensor and source-rights provenance, required citation/attribution, and all storage, user-count, deletion, audit, geographic/export, security, duration, and later-commercial-use conditions. If checkpoints or reproducibility evidence cannot be retained/published, please state that clearly. We will not ingest the sample into training or evaluation until written terms pass internal review. Thank you.

### 3.5 Structural Defects — Bonnín-Pascual / Ortiz

**Route:** Author contact listed on the resource page.  
**Subject:** Dataset permission clarification — Structural Defects use in OceanSense student research

> Dear Dr. Bonnín-Pascual,
>
> We are the OceanSense Conrad Challenge student team, developing a non-commercial research/competition prototype for underwater inspection decision support. We are considering the Structural Defects original/extended RGB images and corresponding ground-truth masks only as supplemental, non-underwater transfer and robustness data for corrosion, cracks, and coating breakdown.
>
> We would request the exact image/mask package, version or file list, annotation documentation, checksums if available, and preferred citation. We do not intend to redistribute raw images or masks publicly; approved files would be held privately. We may resize/preprocess them, create derived condition mappings, and publish trained checkpoints, aggregate/per-class metrics, prediction logs, and a limited number of attributed failure examples.
>
> Could you explicitly confirm in writing who owns/licences the underlying images and masks; whether our Conrad Challenge training/evaluation, judging, demo, pitch, and publication uses are permitted; whether derivatives and checkpoint/results publication are allowed; and what redistribution, storage, access, deletion, or later-commercial-use restrictions apply? Please provide the applicable license URL/text and exact attribution/citation.
>
> We will clearly report the non-underwater domain limitation and preserve all required attribution. We will not use the files until the permission and provenance evidence pass review. Thank you.

### 3.6 WPI / ARL Corrosion

**Route:** Authorized WPI Automation and Robotics Lab dataset maintainer/contact channel.  
**Subject:** License and research-use permission — WPI/ARL Corrosion Dataset for OceanSense

> Hello,
>
> We are the OceanSense Conrad Challenge student team, developing a non-commercial research/competition visual baseline for underwater inspection decision support. We are considering the WPI/ARL Corrosion RGB images, expert ratings/labels, metadata, file manifest, annotation/rating guide, and citation information only as supplemental laboratory/non-underwater corrosion transfer and robustness data.
>
> We do not plan to redistribute raw dataset files publicly; approved assets would be stored privately. We may resize/preprocess images, map ratings to carefully reviewed derived labels, and publish trained checkpoints, aggregate/per-class metrics, prediction logs, and a limited number of attributed failure examples.
>
> Could an authorized owner/licensor provide explicit written permission for Conrad Challenge training/evaluation, judging, demos, pitch materials, and publication? Please confirm that the permission covers the images and labels, derived annotations, checkpoint/results publication, and identify any raw/derived redistribution, storage, access, deletion, geographic/export, time, user-count, or later-commercial-use restrictions.
>
> Please provide the exact covered version/file list, applicable license URL/text, owner/licensor identity, and required citation/attribution. We will retain the evidence, disclose the laboratory domain limitation, and will not use the dataset before internal approval. Thank you.

### 3.7 K-Pipelines — generated-image provenance and license coverage

**Route:** GitHub issue or maintainer contact.  
**Subject:** K-Pipelines generated-image license/provenance clarification — OceanSense student project

> Hello,
>
> We are the OceanSense Conrad Challenge student team, developing a non-commercial research/competition underwater inspection baseline. We are considering K-Pipelines RGB images only as a separately reported synthetic corrosion challenge or supplemental training set. They would never count toward our primary real-image evaluation metrics.
>
> We would request only the generated image files, labels/splits, generation prompts/settings or provenance metadata, file manifest/checksums, and citation information. We do not plan to redistribute raw images publicly unless the applicable terms explicitly allow it. We may store approved files privately, preprocess them, create derived labels, and publish trained checkpoints, synthetic-only metrics, prediction logs, and limited attributed failure examples.
>
> The repository is reported as GPL-3.0, but could you explicitly confirm in writing whether that license covers the generated image assets and labels, who holds the necessary rights to the generation inputs/outputs, and whether the proposed ML training/evaluation, derivatives, checkpoint publication, and result examples are allowed? Please state any source-model/content restrictions, redistribution or share-alike obligations, exact attribution/citation, and the covered repository commit/release and file list.
>
> We will preserve provenance and keep synthetic results separate. We will not use assets whose ownership or license coverage remains unclear. Thank you.

### 3.8 Dryad Biofouling Survey Data — no request queued

No contact message is currently required because this track is limited to the deposited CC0 tabular survey context described by the existing review. Before contextual use, archive the exact record version, DOI, CC0 metadata, file list, citation, and review date. If the record/license snapshot reveals an exception or a desired asset is not part of the deposited tables, use the following clarification:

**Subject:** Dryad record scope clarification — biofouling survey context for OceanSense

> Hello,
>
> We are the OceanSense Conrad Challenge student team and would like to cite the deposited biofouling survey tables only as non-commercial research/competition context. We will not treat tabular data as image-model training or visual evaluation data and do not plan to redistribute a modified dataset.
>
> Could you confirm the exact record version and files covered by CC0, the preferred scholarly citation, and whether any deposited file carries a separate restriction? We may publish aggregate contextual summaries with attribution, but no visual checkpoint or image derivative will be produced from these tables. Thank you.

## 4. License Evidence Requirements

Create one evidence folder per candidate under `data/model1_baseline_v2/licenses/<dataset-id>/`. Before any asset is used, preserve:

| Dataset | Required evidence before use |
|---|---|
| SubPipe | dated record-page and API metadata snapshots; authorized license grant/text/URL; DOI, version, creators, citation, attribution; covered file manifest and exceptions; permitted training/evaluation/derivative/output uses; redistribution limits; review date and named internal approval |
| InspectVQA | dataset-card snapshot; exact version/commit and file list; CC BY-NC 4.0 text or alternative grant; identifiable owner/licensor and authority; complete sent request and response; competition/non-commercial scope; storage/redistribution, derivatives/checkpoint publication, attribution, restrictions, and review date |
| CleanCam | selected record/version and API snapshots; current v2.0.0 resolution; authorized license grant/text/URL; creators/DOI/citation; real-versus-synthetic file manifest; split documentation; allowed derivatives/outputs, redistribution limits, review date, and internal approval |
| Claru | sent inquiry and provider response; sample terms; signed contract/order if proceeding; licensor/source-rights statement; covered files/version; price/term; allowed use; storage/deletion/access/export restrictions; raw/derived redistribution and checkpoint/result publication rights; attribution; review date |
| Structural Defects | page snapshot and citation; exact image/mask file list; explicit owner/licensor response and license text; training/evaluation and competition permission; derivatives, checkpoint/results/examples rights; redistribution/storage limits; review date |
| WPI / ARL Corrosion | page snapshot and citation; exact version/file list and ratings guide; authorized-owner response/license; permitted use and derivatives; checkpoint/results publication; redistribution/storage/access restrictions; attribution and review date |
| K-Pipelines | repository commit/release and license snapshot; generated-image asset coverage; generation provenance and source-rights statement; file manifest; synthetic flag; training/output and redistribution/share-alike obligations; attribution and review date |
| Dryad | DOI/version record and CC0 snapshot; deposited file list; citation; confirmation that only tabular context is used; any exceptions; review date; no image-evaluation approval row |

Every folder must additionally record the license URL, screenshot or downloaded metadata snapshot, exact citation text, owner approval email/message where required, allowed use, redistribution limits, derivative/checkpoint publication limits, attribution requirements, and `date_reviewed`. Preserve evidence in its original format plus a plain-text summary; hash all files and cite them from the future approved manifest.

## 5. Approval Decision Rules

### Approved for primary evaluation

A dataset or asset subset may enter the primary real RGB evaluation snapshot only when:

1. the underlying images and annotations are explicitly covered by an authoritative license or written grant;
2. Conrad competition, non-commercial research, evaluation, private storage, required transformations, derived labels, and evidence retention are permitted;
3. publication of the intended checkpoint/metrics/predictions/failure examples is permitted or the output restrictions are compatible with the plan;
4. version, source, owner/licensor, citation, attribution, file list, hashes, and restrictions are archived;
5. every asset is real RGB, maps legitimately to the Model 1 schema after dual review, passes provenance/quality/duplicate checks, and is assigned to an immutable group-independent split;
6. a named reviewer marks the manifest row `approved`; and
7. no synthetic, tabular-only, sonar-only, or unresolved-rights item is counted toward the 270-image minimum.

No currently tracked dataset satisfies all seven gates.

### Approved only for supplemental testing

Use this status when rights are complete but the data is synthetic, non-underwater/laboratory, camera-condition rather than structural ground truth, strongly domain-shifted, or context-limited. Results must be isolated and labeled by source/origin. K-Pipelines can only be synthetic supplemental; Structural Defects and WPI only transfer/robustness; CleanCam only visibility/fouling/camera-degradation robustness unless a separately reviewed real-image mapping supports another claim; Dryad remains context, not visual testing.

### Rejected

Reject a source or asset if ownership/authority cannot be verified; license terms prohibit the intended use/evidence retention; raw-image rights do not cover the files; required attribution or restrictions cannot be met; provenance is missing; labels cannot be mapped without fabrication; leakage/duplication cannot be resolved; the contract is unaffordable or incompatible; or the provider refuses necessary clarification. Record the reason and evidence; never rename rejection as approval.

### Legal/owner clarification required

Keep status `MANUAL_REVIEW_REQUIRED` whenever license scope, dataset version, third-party content, non-commercial/competition meaning, derivatives, checkpoint publication, failure examples, storage/redistribution, source rights, or respondent authority is unclear. Silence, a web download button, a citation request, or a repository code license is not sufficient clarification.

## 6. File Storage Plan After Approval

Do not create downloaded dataset content during this task. After authorization, use:

```text
data/model1_baseline_v2/
  raw/
    <dataset-id>/<immutable-version>/
  processed/
    images/
    annotation_audit.csv
  licenses/
    <dataset-id>/
      request.txt
      response.txt
      record_snapshot.html
      metadata.json
      license.txt
      attribution.txt
      review.md
      checksums.sha256
  manifests/
    source_assets.csv
    approved_assets.csv
    checksums.sha256
  splits/
    split.csv
    split_audit.md
  README.md
```

`raw/` is immutable and access-controlled. `processed/` contains only derived, approved assets. `licenses/` preserves original and summarized evidence. `manifests/` binds every asset to rights, provenance, hashes, approval, and real/synthetic status. `splits/` preserves group-independent assignments and leakage review. `README.md` records version, sources, schema, permitted uses, exclusions, limitations, attribution, and maintainers.

The canonical fallback files from `docs/MODEL1_BASELINE_V2_FALLBACK_PLAN.md` remain `data/model1_baseline_v2/manifest.csv`, `labels.csv`, and `split.csv`; the richer folders above support their evidence chain. If compatibility copies are produced, their hashes must match the canonical files and the README must explain the relationship.

## 7. Next Gate

**send requests manually**

Recommended order:

1. Send InspectVQA permission request and Structural Defects/WPI license requests immediately.
2. Send the required SubPipe and CleanCam license/file-scope clarification and archive verifiable receipts and responses.
3. Send the Claru inquiry only after a human confirms budget and acceptable contract constraints.
4. Send the K-Pipelines provenance question if synthetic supplemental testing remains useful.
5. Archive Dryad metadata as `CONTEXT_ONLY`; do not request or create visual rows.

After each manual send, update this log with evidence instead of changing the executive status based on memory. The next status may become **REQUESTS SENT** only when at least one verifiable send receipt exists. Do not download any dataset until its relevant license/permission and internal approval evidence are recorded.

## Integrity and Scope Statement

No request was sent by this repository task. No approval was inferred from public availability. No external dataset or dataset archive was downloaded. No labels, metrics, checkpoints, responses, receipts, license files, or approvals were fabricated. No Model 1 training was run. No Model 2 or Twin 2 work was performed. Original Model 1 remains blocked/not frozen, and `model1_baseline_v2` remains an inactive fallback until its activation gate is met.
