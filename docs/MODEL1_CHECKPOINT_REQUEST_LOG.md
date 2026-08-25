# Model 1 Checkpoint Recovery Request Log

## Current Request State

**READY_FOR_HUMAN_SEND**

The appropriate recipient is the original Model 1 trainer, run owner, or team member who controls the original training machine, cloud notebook output, artifact store, external drive, or backup. That person is not identified in the repository or current contact evidence. Kerem or a co-founder who knows the original trainer must identify that owner and send the exact message in this log.

Burak Ata Aksu is explicitly **not** the recovery source: the team has confirmed that Burak has no checkpoint files, dataset package, or original Model 1 evaluation files locally. Do not ask Burak to upload files and do not send him another recovery request.

| Field | Current value |
|---|---|
| Request state | **READY_FOR_HUMAN_SEND** |
| Appropriate recipient | Original Model 1 trainer/artifact owner — identity and direct channel not yet known |
| Human sender required | Kerem or the co-founder/team member who can identify the original trainer/artifact owner |
| Appropriate-owner send status | **NOT SENT** |
| Response status | No response from an appropriate package owner |
| Files received | **No** |
| Recovery deadline | 2026-09-01 17:00 Europe/Istanbul |
| Immediate action | Identify the original trainer/artifact owner and send the message on 2026-08-26 |
| Next follow-up date | 2026-08-28 17:00 Europe/Istanbul; if still unsent, escalate contact identification rather than contacting Burak |

## Prior Misdirected Contact Record

On 2026-08-25 at 23:57 Europe/Istanbul, the earlier version of this request was delivered by WhatsApp direct message to Burak Ata Aksu. Burak has since been confirmed to have none of the requested local files. That historical transmission is retained for audit accuracy, but it does **not** satisfy the recovery request to the appropriate original owner and must not be followed by a file-upload request to Burak.

## Exact Message Ready for Human Send

```text
Hi, we’re finalizing the Conrad Model 1 baseline review and need to recover the original evaluation package.

Do you have these files from the original Model 1 training/evaluation run?

- models/oceansense_domain_efficientnet_b0.pt
- models/oceansense_condition_efficientnet_b0.pt
- approved image manifest or dataset folder
- real labels.csv
- train/validation/test split
- evaluation config
- metrics output
- prediction/failure examples
- license/access proof for the dataset

The repo has the architecture, preprocessing, class schema, split tooling, and eval script, but not the actual checkpoints/evaluation package. Without these, we can’t validate or freeze original Model 1.

Can you send the package or tell us where it’s stored by Sep 1, 2026, 17:00 Europe/Istanbul? If we can’t recover it by then, we’ll keep original Model 1 blocked/not frozen and move to model1_baseline_v2.
```

## Files Still Outstanding

All requested artifacts remain missing:

- `models/oceansense_domain_efficientnet_b0.pt`;
- `models/oceansense_condition_efficientnet_b0.pt`;
- approved image manifest or dataset folder;
- real `labels.csv`;
- immutable train/validation/test split;
- evaluation configuration;
- metrics output;
- prediction and failure examples;
- dataset license/access proof.

No checkpoint may be marked recovered until the exact file exists locally and passes the documented Model 1 loading-contract validation. A package location, promise, navigation ONNX file, renamed weight, placeholder, or partial archive is not recovery evidence.

## Request Loop

1. **Identify:** Kerem or the relevant co-founder identifies the original trainer/artifact owner and a direct WhatsApp, email, or team-channel route.
2. **Send:** The human sender transmits the exact message above without asking Burak to upload anything.
3. **Record:** Add the actual recipient, channel, send timestamp, delivery/receipt evidence, and response status to this log. Only then change the state to `SENT`.
4. **Follow up:** If sent but unanswered, follow up on 2026-08-28 at 17:00 Europe/Istanbul. If the owner is still unidentified, escalate within the team on the same date to locate the original machine, cloud notebook, artifact store, external drive, or backup owner.
5. **Validate:** If files arrive, preserve provenance and hashes, validate both checkpoint payloads against the EfficientNet-B0 loading contract, and verify the supporting package before changing any recovery status.
6. **Decide at deadline:** If the complete valid package is not recovered by 2026-09-01 at 17:00 Europe/Istanbul, original Model 1 remains **BLOCKED / NOT FROZEN**. The project may proceed only through the separately gated `model1_baseline_v2` new-training path; this is not validation or freezing of the original model.

## Integrity Statement

No requested file has been received or verified. The appropriate-owner request has not been sent because the owner/contact is not yet identified. No checkpoint is marked recovered, no Model 1 freeze is claimed, no dataset was downloaded, and no training or Model 2/Twin 2 work was performed.
