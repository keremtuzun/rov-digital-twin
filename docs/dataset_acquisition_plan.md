# License-gated dataset acquisition plan

Reviewed against official project/source pages on 2026-08-23. No large asset was downloaded. The
automatic allowlist is Public Domain, CC0 and CC BY 4.0; every asset still needs checksum, caption,
credit, source URL and reviewer identity.

## Candidate sources

### NOAA Ocean Exploration Video Portal — ready for asset review

The official data-access page states that all portal video is public domain and provides ROV dive
metadata/downloads. Use as normal/negative underwater, habitat, seabed and ROV-domain footage. Retain
the exact caption/credit and reject any individually marked copyrighted exception.

- Official: https://oceanexplorer.noaa.gov/data/access/
- Status: source approved; each chosen asset still reviewed and manifested.

### TrashCan 1.0 — manual review

IRVLab documents 7,212 annotated images and says imagery originates in JAMSTEC J-EDI. IRVLab's resource
page also describes its datasets as academic-research-only. That is outside the automatic allowlist,
and the upstream J-EDI image terms must be reconciled separately.

- Official: https://irvlab.cs.umn.edu/resources/trashcan
- Repository record: https://conservancy.umn.edu/handle/11299/214865
- Status: manual review; no automatic ingestion.

### SUIM — manual review

The repository describes 1,525 train/validation and 110 test images, but a repository/code license is
not evidence of permission for every dataset image. IRVLab's research-only resource statement also
applies. Do not ingest until an explicit image-dataset license is recorded.

- Official: https://github.com/IRVLab/SUIM
- Status: manual review.

### FathomNet — per-asset filtering

The current terms allow contributors to select CC0, CC BY, CC BY-NC or CC BY-NC-ND for visual assets;
copyright stays with contributors. Query only assets whose exact license is CC0 or CC BY 4.0 and store
that license/attribution per image. NC/ND assets remain manual review.

- Official terms: https://www.fathomnet.org/terms
- Status: potentially ready through strict per-asset filtering; API/account/size approval still needed.

### DeepFish — manual review

The official project page links the Queensland data record but does not display a license itself.
Require the downloadable record's explicit license and attribution before any automated retrieval.

- Official: https://alzayats.github.io/DeepFish/
- Status: manual review.

### CoralNet — annotation service, source-specific review

CoralNet supports public and private sources and an API, but public visibility does not establish that
an image owner granted the intended reuse license. Use it primarily for permissioned expert annotation;
record source membership, owner and export permission.

- Official/API: https://coralnet.ucsd.edu/pages/help/api/
- Status: manual review per source.

### Institution-owned capture — preferred structural path

For pipes, welds, metal surfaces, biofouling, corrosion-like appearance, nets and cages, collect
permissioned pool/marina/operator footage with calibration targets, varied lighting/turbidity/distance,
mission IDs and dual expert review. Preserve permits and releases in the license register.

Reliable open underwater crack/corrosion data has not been established. Terrestrial crack datasets may
support explicitly labelled pretraining/domain-adaptation experiments, never the untouched underwater
test set and never a real-field structural claim.

## Acquisition gate

1. Populate raw manifest metadata without downloading.
2. Save applicable license evidence and verify upstream terms.
3. Show asset count, class/source distribution, estimated bytes/time and requested API limits.
4. Obtain user approval for large download or external service use.
5. Download only audited rows with resume, delay, robots and SHA-256 checks.
6. Split by mission/video, then reserve a source-independent external real test set.

Prototype target is 200–500 approved examples per retained canonical class (roughly 2,000–5,000 total),
not a success guarantee. Reduce classes when those counts or expert labels are unavailable.
