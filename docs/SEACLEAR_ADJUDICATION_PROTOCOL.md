# SeaClear Adjudication Protocol

**Status:** `READY — NO ADJUDICATIONS PERFORMED`

## 1. When adjudication is required

Set `review_status=needs_adjudication` when two complete independent reviews disagree on domain or condition, either reviewer records genuine ambiguity, a proposed source mapping conflicts with visible context, an unknown/rejection decision conflicts with a canonical label, or the data approver identifies a material evidence inconsistency.

Matching reviews do not require adjudication but still require validation and data-approver authorization before `approved`.

## 2. Who may adjudicate

The adjudicator must:

- use a stable recorded identity;
- differ from Reviewer 1 and Reviewer 2 for that row;
- understand the Model 1 domain/condition guide and non-diagnostic claim boundary;
- have access to the immutable full-resolution image, source annotations, both independent reviews, license/provenance evidence, and relevant neighboring-frame context where available;
- disclose conflicts of interest or inability to decide.

Structural/ecological/aquaculture ambiguity should be escalated to a reviewer with relevant domain expertise. An agent-generated suggestion cannot act as adjudicator.

## 3. Evidence inspected

Before deciding, verify `review_id`, image ID/path, SHA-256, site/camera group, all source annotation IDs/categories, full RGB frame, both reviewer labels/notes/timestamps, labeling guide, and any duplicate/provenance flags. Do not inspect training predictions or desired class counts; those would bias ground truth.

## 4. Decision procedure

1. Confirm both reviews are complete, independent, attributable, and use valid UTC timestamps.
2. Identify the exact disagreement: domain, condition, rejection, visibility interpretation, or source mapping.
3. Inspect visible evidence without treating COCO categories or suggestions as final truth.
4. Select one canonical domain and one canonical condition only when supported.
5. If evidence remains indeterminate, choose `unknown` with explanatory notes or reject with a schema-listed reason.
6. Record `adjudicator_id`, `adjudicated_domain`, `adjudicated_label`, evidence-based `adjudicator_notes`, and `adjudication_timestamp`.
7. Run `python scripts/build_seaclear_review_queue.py --validate-only`.
8. A data approver separately verifies hash/license/audit evidence and sets intended-use flags. The adjudicator does not silently authorize training/test use.

## 5. Approval and rejection rules

- A resolved disagreement may become `approved` only with complete adjudication, validator success, and at least one explicit data-approver use flag.
- A row becomes `rejected` when no reliable canonical label is possible, quality/provenance is unacceptable, or evidence is outside Model 1 scope. Record `rejection_reason`; all use flags stay `false`.
- `unknown` is a valid label for genuine indeterminacy, not a way to avoid rejection or meet class counts.
- Test eligibility receives the strictest review. Synthetic images are never primary-test eligible.
- Approval for one role does not imply approval for another role.

## 6. Audit trail and versioning

Never overwrite reviewer submissions, delete disagreement history, change raw files, or reuse a review ID for a different hash. Corrections create a versioned queue/audit entry that records previous/new values, reason, actor, timestamp, and affected dataset/split versions.

The future `docs/SEACLEAR_LABEL_APPROVAL_AUDIT.md` must report reviewed/approved/rejected/pending/adjudication counts, agreement rate before adjudication, per-class and intended-use counts, queue/schema/source hashes, reviewer/adjudicator identities, evidence locations, exceptions, and remaining blockers. Until that real audit exists and passes, SeaClear labels are not an approved Model 1 dataset.

## 7. Current decision

No human reviews or adjudications were supplied in Step 10. Therefore all 8,610 rows remain `pending_review`, all use flags are `false`, approved label count is zero, and Model 1 remains **BLOCKED / NOT FROZEN**.
