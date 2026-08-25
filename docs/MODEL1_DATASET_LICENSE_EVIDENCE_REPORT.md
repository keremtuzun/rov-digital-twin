# Model 1 Dataset License Evidence Report

**Reviewed:** 2026-08-26  
**Scope:** SubPipe and CleanCam metadata/version/license gate  
**Result:** `BOTH_REQUIRE_OWNER_OR_LICENSOR_CLARIFICATION`

## Decision summary

| Candidate | Version reviewed | Official record evidence | License field | Approval |
|---|---|---|---|---|
| SubPipe | `3.0.1` | DOI, creators, description, three file names/sizes/checksums | API `metadata.rights` is `null` | Not approved |
| CleanCam | current `v2.0.0` | DOI, creators, description, one file name/size/checksum | API `metadata.rights` is `null` | Not approved; supplemental-only role if later approved |

The repository previously repeated CC BY 4.0 for both candidates. The current official-record/API inspection does not substantiate that claim. Zenodo documents CC BY 4.0 as its default deposit choice, but a platform default is not a record-specific license grant. The safe decision is therefore to remove the assumed license and request written, file-scoped confirmation.

## Evidence archived

- `data/model1_baseline_v2/licenses/subpipe/README.md`
- `data/model1_baseline_v2/licenses/cleancam/README.md`

These are metadata review summaries, not dataset approval records. No raw images, archives, labels, checkpoints, or synthetic artifacts were downloaded or created.

## Next gate

1. A human sends the already prepared clarification to an authorized SubPipe owner/licensor and CleanCam maintainer.
2. Archive a verifiable sent receipt and the complete response.
3. Confirm respondent authority, exact covered version/files, license text/URL, intended ML and competition uses, transformations, checkpoint/results publication, example-image use, attribution, storage, and redistribution.
4. A named internal reviewer approves or rejects the evidence.
5. Only then may approved assets enter the manifest and immutable split workflow.

Until this gate passes, both candidates remain excluded from training and evaluation.
