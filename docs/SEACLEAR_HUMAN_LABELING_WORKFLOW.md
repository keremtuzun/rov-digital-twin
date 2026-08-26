# SeaClear Human Labeling Workflow

**Prepared:** 2026-08-26

**Workflow status:** `READY_FOR_HUMAN_REVIEW`

**Model 1 status:** **BLOCKED / NOT FROZEN**

## 1. Purpose and evidence boundary

This workflow converts the 8,610-row SeaClear staging inventory into independently reviewed candidate evidence for the two-head Model 1 schema. It does not approve labels, activate training, create a canonical split, validate the original missing Model 1, or freeze a model.

Initial queue evidence:

- Queue: `data/model1_baseline_v2/manifests/label_review_queue.csv`
- Queue rows: 8,610
- Queue SHA-256: `45ca6880fa4f5113d15d4a740167aa981a34f4d4bed3e471741bf41df1aa6a71`
- Schema: `data/model1_baseline_v2/manifests/label_review_schema.json`
- Schema SHA-256: `dbf269ab80d0e26d28fcc7bc14001634b88aecb9122614da7eadefad8a5644e7`
- Source annotation IDs represented: 31,555
- Initial status: 8,610 `pending_review`; zero approval-use flags

The raw JPEGs remain under Git-ignored `data/model1_baseline_v2/raw/seaclear/v1/`. Reviewers must not rename, edit, recompress, move, or overwrite them.

## 2. Roles

| Role | Responsibility | Independence rule |
|---|---|---|
| Review coordinator | Freezes queue/schema hashes, assigns batches, creates access-controlled blinded views, merges submissions by `review_id` and hash | Cannot silently change reviewer decisions |
| Reviewer 1 | Independently assigns domain and condition using the full RGB frame and guide | Cannot see Reviewer 2 fields before submission |
| Reviewer 2 | Independently repeats the same review | Cannot see Reviewer 1 fields before submission |
| Adjudicator | Resolves disagreements/ambiguous cases using both reviews and source evidence | Must differ from both reviewers for the row |
| Data approver/steward | Runs validation, verifies license/hash/audit evidence, and authorizes use flags | Cannot infer approval from source suggestions or reviewer agreement alone |

Every person must use a stable non-empty identifier. Shared identities such as `team`, `reviewer`, or `admin` are not acceptable.

## 3. Reproducing and validating the initial queue

Generate only before human review begins:

```powershell
python scripts/build_seaclear_review_queue.py
```

The command refuses to overwrite an existing queue. `--force` exists only for a verified pre-review rebuild and must never be used after a reviewer submission. Validate without mutation:

```powershell
python scripts/build_seaclear_review_queue.py --validate-only
```

The queue is joined by `source_image_id`, not row position. COCO annotation IDs are sorted and stored in `source_annotation_ids`; source suggestions remain non-binding.

## 4. Blinded double-review execution

1. Coordinator records the queue/schema hashes and assigns non-overlapping batches by `review_id`.
2. Coordinator creates two access-controlled views or copies. Both contain source fields, suggestion fields, and only the receiving reviewer's writable fields. Reviewer 1 must not receive Reviewer 2 columns or submissions, and vice versa.
3. Each reviewer opens the immutable image resolved by `image_path_or_relative_key`, confirms `image_sha256` when tooling permits, inspects the complete frame, and submits domain, condition, notes, ID, and UTC timestamp.
4. Reviewer submissions are merged only by `review_id` plus `image_sha256`. A path/hash mismatch blocks the row.
5. A row remains `pending_review` while either independent review is incomplete.
6. When both reviews are complete:
   - exact domain and condition agreement proceeds to validation and data-approver review;
   - any domain or condition disagreement becomes `needs_adjudication`;
   - an unresolved/unclear case remains blocked and cannot receive an approval flag.
7. Exact agreement may be promoted to `approved` only after the queue validator passes, the data approver verifies rights/hash/evidence, required notes exist, and at least one explicit intended-use flag is recorded. Agreement alone is not approval.
8. Rejected rows use `rejected`, a schema-listed `rejection_reason`, and explanatory reviewer/adjudicator notes. All use flags remain `false`.

## 5. Status transitions

| Current state | Required evidence | Next state |
|---|---|---|
| `pending_review` | Reviewer 1 only or no reviews | `pending_review` |
| `pending_review` | Two complete matching reviews plus successful validation/steward decision | `approved` or `rejected` |
| `pending_review` | Two complete disagreeing reviews | `needs_adjudication` |
| `needs_adjudication` | Independent adjudicator final domain/label, notes, timestamp, validation, steward decision | `approved` or `rejected` |
| `needs_adjudication` | Evidence remains unclear | stays blocked; no approvals |
| `approved` | Immutable audit/split process | may enter canonical package for explicitly true use roles |
| `rejected` | New evidence or corrected source requires a versioned re-review | never silently reopened |

## 6. Queue integrity rules

- `review_id`, `image_id`, path, and SHA-256 are non-empty and unique.
- Reviewer IDs are distinct; an adjudicator is different from both reviewers.
- Timestamps use UTC RFC3339: `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`.
- `unknown`, ambiguous, or rejected decisions require meaningful notes.
- Pending/adjudication/rejected rows cannot carry a `true` approval flag.
- An approved disagreement requires complete adjudication evidence.
- Suggestions may be hidden from reviewers to reduce anchoring; they never count as a vote.
- Raw source annotations and images are immutable. Corrections create a versioned queue and audit entry.

## 7. Dataset split gate

Split creation is forbidden until the reviewed queue, approved canonical labels, rejection list, adjudication records, source/image checksums, and license/citation evidence exist and pass audit.

When allowed:

- group by mission/site/camera and keep adjacent/near-duplicate frames together;
- detect exact and perceptual duplicates before assignment;
- never permit an image or near-duplicate across splits;
- meet the locked real-image floors for all six domains and nine conditions;
- keep the test set hidden from training, augmentation, threshold selection, and model selection;
- record seed, grouping rule, snapshot/version, row assignments, and SHA-256;
- treat any later row/split change as a new dataset version that invalidates prior test claims.

## 8. Model 1 preflight gate

Model 1 training/evaluation remains blocked until all of the following are real and verified:

- approved canonical `data/model1_baseline_v2/labels.csv`;
- approved canonical `manifest.csv` with asset-level rights and hashes;
- immutable/checksummed group-aware `split.csv`;
- complete annotation review/adjudication evidence;
- license/citation evidence and dataset checksum manifest;
- dataset validation/audit declaring the exact snapshot approved;
- valid fallback activation authorization under the configured reason;
- original checkpoint recovery decision preserved as **BLOCKED / NOT FROZEN**;
- all class floors and real-only primary-test requirements passing.

The current `scripts/preflight_model1_baseline_v2.py` must continue returning `ready: false`. The review queue is preparation evidence, not a substitute for any canonical file.

## 9. Required future approval audit

Create `docs/SEACLEAR_LABEL_APPROVAL_AUDIT.md` only after real reviewer evidence exists. It must record queue/schema/source hashes, reviewer identities, images reviewed/approved/rejected/pending/adjudication counts, agreement rate, per-domain/per-condition counts, intended-use counts, split counts, evidence paths, exceptions, and remaining blockers. Its final decision must be `APPROVED`, `NOT APPROVED`, or `BLOCKED`.

This task intentionally does not create a fulfilled approval audit, approved `labels.csv`, or training checkpoint.
