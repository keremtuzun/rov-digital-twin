# Model 1 Remaining Dataset Request Execution Report

**Reviewed:** 2026-08-26  
**State:** `READY_FOR_AUTHENTICATED_SEND`

## Verified destinations

| Dataset | Destination | Message status | Send status | Blocker |
|---|---|---|---|---|
| InspectVQA | <https://huggingface.co/datasets/anonymousSubmissionVqa2026/InspectVQA/discussions/new> | Exact title/body prepared in the permission log | Not sent | Hugging Face login required in the available browser |
| Structural Defects | `xisco.bonnin@uib.es` (published UIB/SRV contact) | Exact subject/body prepared in the permission log | Not sent | Authenticated email session unavailable |
| WPI / ARL Corrosion | `gr-wpi-arl-dsrg@wpi.edu` (published dataset contact) | Exact subject/body prepared in the permission log | Not sent | Authenticated email session unavailable |

## Evidence boundary

- The InspectVQA dataset card currently states `CC BY-NC 4.0, or another license approved by the data owner`, but the publisher identity/authority and Conrad competition/output scope remain unresolved.
- The Structural Defects resource page publishes the named UIB contact, image/mask downloads, and citation, but not an explicit dataset reuse license covering the intended ML outputs.
- The WPI/ARL page publishes its group contact, download/citation instructions, and an MIT notice, but written confirmation is still required that the exact image/label package and intended model outputs are covered.
- No message was sent, no file was downloaded, and no approval was inferred in this step.

## Resume instruction

Reconnect the user's authenticated Chrome browser, then prepare all three forms and request one grouped action-time confirmation immediately before publishing/sending them. After sending, record the public discussion URL or email sent timestamps, response status, and a five-business-day follow-up date in `docs/MODEL1_DATASET_PERMISSION_EXECUTION_LOG.md`.
