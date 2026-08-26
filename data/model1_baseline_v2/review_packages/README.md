# SeaClear blinded reviewer packages

These are immutable, condition-label review templates for two independent human reviewers. They do not contain approved labels and do not make SeaClear eligible for training, validation, or testing. Model 1 remains **BLOCKED** and **NOT FROZEN**.

## Package record

- Generated: `2026-08-26T17:21:19.440336Z` (`2026-08-26 20:21:19 Europe/Istanbul`)
- Source queue: `data/model1_baseline_v2/manifests/label_review_queue.csv`
- Source queue SHA-256: `45ca6880fa4f5113d15d4a740167aa981a34f4d4bed3e471741bf41df1aa6a71`
- Reviewer 1 queue: `reviewer_1_queue.csv` — 8,610 rows — seed `1101`
- Reviewer 1 SHA-256: `f7f655873cbc1696c679e0733bf74c14a8c3c37d9292718d2113f792f90b889f`
- Reviewer 2 queue: `reviewer_2_queue.csv` — 8,610 rows — seed `1102`
- Reviewer 2 SHA-256: `859e1c990a5ed44c4995edba6f30a5d6b08211c31780265008db033459f4019a`
- Machine-readable record: `package_manifest.json`
- Checksum sidecars: `reviewer_1_queue.csv.sha256`, `reviewer_2_queue.csv.sha256`

Both files contain the same 8,610 review IDs and image identities in independently and reproducibly shuffled orders. Each has one generic set of blank reviewer fields. Neither file contains reviewer identity, the other reviewer's work, adjudication data, approval flags, or split assignments.

## Use

Assign one file to each reviewer without sharing the other file or any completed submission. Reviewers should work on a copy and leave these hashed templates unchanged. Follow `docs/SEACLEAR_REVIEWER_ASSIGNMENT_INSTRUCTIONS.md` and `docs/SEACLEAR_LABELING_GUIDE.md`.

The packages collect condition labels only. They do not approve a condition label, review the Model 1 domain label, adjudicate disagreement, create `labels.csv`, or authorize training. Completed submissions must be validated and reconciled through the documented human workflow before any separate approval decision.

Reproduce before review begins with:

```powershell
python scripts/build_seaclear_reviewer_packages.py --force
```

Validate the immutable templates with:

```powershell
python scripts/build_seaclear_reviewer_packages.py --validate-only
```

Never use `--force` after either reviewer starts work.
