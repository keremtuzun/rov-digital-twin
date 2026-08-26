# Model 1 Remaining Dataset Request Execution Report

**Reviewed:** 2026-08-26  
**State:** `SUPERSEDED_BY_USER_OPEN_LICENSE_DIRECTION`

## Verified destinations

| Dataset | Destination | Message status | Send status | Blocker |
|---|---|---|---|---|
| InspectVQA | <https://huggingface.co/datasets/anonymousSubmissionVqa2026/InspectVQA/discussions/new> | Prepared only | `DO_NOT_SEND_USER_DIRECTED` | Replaced with open-license sourcing |
| Structural Defects | `xisco.bonnin@uib.es` (published UIB/SRV contact) | Prepared only | `DO_NOT_SEND_USER_DIRECTED` | Replaced with open-license sourcing |
| WPI / ARL Corrosion | `gr-wpi-arl-dsrg@wpi.edu` (published dataset contact) | Prepared only | `DO_NOT_SEND_USER_DIRECTED` | Replaced with open-license sourcing |

## Evidence boundary

- The InspectVQA dataset card currently states `CC BY-NC 4.0, or another license approved by the data owner`, but the publisher identity/authority and Conrad competition/output scope remain unresolved.
- The Structural Defects resource page publishes the named UIB contact, image/mask downloads, and citation, but not an explicit dataset reuse license covering the intended ML outputs.
- The WPI/ARL page publishes its group contact, download/citation instructions, and an MIT notice, but written confirmation is still required that the exact image/label package and intended model outputs are covered.
- None of these three prepared messages was sent, and no approval was inferred. SeaClear was later downloaded through the superseding open-license action documented below.

## Superseding action

On 2026-08-26 the user instructed the project not to send the InspectVQA or WPI/ARL requests and to obtain data from open sources instead. Structural Defects was paused under the same open-license strategy. SeaClear v1 was subsequently acquired from 4TU.ResearchData and hash-verified; see `docs/MODEL1_SEACLEAR_ACQUISITION_REPORT.md`.
