# SeaClear submission intake and comparison

## Current status

The tooling is ready, but no completed human submissions were present when it was created. No comparison artifacts, approved labels, or `labels.csv` were generated. SeaClear remains unapproved, and Model 1 remains **BLOCKED / NOT FROZEN**.

## Purpose and timing

Run this tool only after two different reviewers have independently completed and locked their assigned Step 11 CSVs. It validates each submission against its immutable reviewer package, compares valid decisions by `review_id`, and creates non-approval agreement, disagreement, invalid-row, and adjudication artifacts.

Agreement is reviewer evidence, not dataset approval. The tool never creates `labels.csv`, assigns train/validation/test eligibility, freezes Model 1, or authorizes training.

## Required inputs

Default completed-submission paths:

- `data/model1_baseline_v2/review_submissions/reviewer_1_completed.csv`
- `data/model1_baseline_v2/review_submissions/reviewer_2_completed.csv`

Immutable references:

- `data/model1_baseline_v2/review_packages/reviewer_1_queue.csv`
- `data/model1_baseline_v2/review_packages/reviewer_2_queue.csv`
- `data/model1_baseline_v2/manifests/label_review_schema.json`

The central JSON schema supplies the authoritative Model 1 condition-label values. The reduced Step 11 package contract supplies the exact permitted submission columns. This separation preserves reviewer blinding while retaining the canonical taxonomy.

Before intake, the coordinator must record reviewer identity, assignment, receipt timestamp, and submission SHA-256 outside the blinded CSV. Never overwrite the original queue templates.

## Run command

```powershell
python scripts/compare_seaclear_reviewer_submissions.py --strict
```

Override paths when needed:

```powershell
python scripts/compare_seaclear_reviewer_submissions.py `
  --reviewer-1 path/to/reviewer_1_completed.csv `
  --reviewer-2 path/to/reviewer_2_completed.csv `
  --package-dir data/model1_baseline_v2/review_packages `
  --schema data/model1_baseline_v2/manifests/label_review_schema.json `
  --output-dir data/model1_baseline_v2/review_results `
  --strict
```

`--strict` exits nonzero if either submission fails validation. Missing inputs always exit nonzero and do not invent submissions or results. Without `--strict`, invalid-row evidence can be written for investigation, but the summary remains `VALIDATION_FAILED` and nothing is approved.

## Validation rules

Each completed file must preserve exactly the 15 Step 11 columns. Extra columns—including approval, split, adjudication, hidden metadata, or fields from the other reviewer—cause a fail-closed structural error. The validator also requires:

- exactly the package row count, with every expected `review_id` once and no unexpected IDs;
- unchanged `image_id`, `image_sha256`, path, provenance, source-category, suggestion, and suggestion-confidence values;
- one allowed reviewer decision and `high`, `medium`, or `low` confidence per row;
- one allowed Model 1 condition label when the decision requires a label;
- an RFC3339 UTC timestamp ending in `Z`;
- notes for `reject_image`, `mark_unknown`, `needs_adjudication`, and every low-confidence decision;
- `approve_suggestion` to copy the suggestion exactly;
- `change_label` to use a different allowed label;
- `reject_image` to leave the label blank;
- `mark_unknown` to use the `unknown` label.

Any identity/hash mismatch, duplicate, missing row, malformed decision, or forbidden column is recorded in `reviewer_invalid_rows.csv`. A row is compared only if both corresponding submissions pass validation.

## Comparison classes

| Class | Meaning |
| --- | --- |
| `agreement_approve` | Both reviewers used the same affirmative decision type and the same final label. |
| `agreement_reject` | Both independently chose `reject_image`. |
| `agreement_unknown` | Both independently chose `mark_unknown`. |
| `disagreement_label` | Decision types match, but final labels differ. |
| `disagreement_decision` | Decision types differ, including reject/unknown versus a label decision. |
| `needs_adjudication` | At least one reviewer explicitly requested adjudication. |
| `invalid` | One or both inputs failed row or file validation; represented in the invalid-row output rather than compared. |

All disagreement classes and explicit adjudication requests enter the adjudication queue. Adjudicator fields are blank on generation.

## Outputs

When both completed input files exist, the tool writes:

- `reviewer_comparison_summary.json`: paths, hashes, counts, agreement rate, per-label counts, timestamp, Git commit, and explicit zero approved-label count;
- `reviewer_agreements.csv`: valid agreements only;
- `reviewer_disagreements.csv`: label/decision disagreements and explicit escalation requests;
- `adjudication_queue.csv`: the required evidence from both reviewers plus blank adjudicator fields;
- `reviewer_invalid_rows.csv`: reviewer, row identity, error code, and explanation.

The reported agreement rate is all valid agreement classes divided by all rows valid for both reviewers. Rejection and unknown counts mean rows where either reviewer selected that decision. Per-label counts are reported separately for each reviewer and for agreements.

## After comparison

The coordinator verifies the summary and hashes, resolves all invalid intake issues without overwriting original submissions, and assigns every adjudication row to a qualified third person under `docs/SEACLEAR_ADJUDICATION_PROTOCOL.md`. Even perfect reviewer agreement does not make labels final. Domain-label review, real adjudication where required, provenance/permission evidence, a formal label-approval audit, immutable splitting, and all baseline gates remain required before Model 1 training.
