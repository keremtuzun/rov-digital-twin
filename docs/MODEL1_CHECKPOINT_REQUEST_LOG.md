# Model 1 Checkpoint Recovery Request Log

## Current Status

| Field | Value |
|---|---|
| Request status | **SENT — DELIVERED, AWAITING RESPONSE** |
| Date/time sent | 2026-08-25 23:57 Europe/Istanbul (2026-08-25 20:57 UTC) |
| Recipient/contact | Burak Ata Aksu |
| Channel | WhatsApp Web, direct message |
| Delivery evidence | WhatsApp displayed `Delivered` for the message at 23:57 |
| Response status | No response received at log creation |
| Recovery deadline | 2026-09-01 17:00 Europe/Istanbul |
| Next follow-up | 2026-08-28 17:00 Europe/Istanbul, unless a response arrives earlier |
| Files received | **No** |

The recipient was selected after the repository contained no original-trainer contact and WhatsApp search showed the Conrad/OceanSense work in the Burak Ata Aksu conversation. The user explicitly confirmed this recipient before transmission.

## Exact Message Sent

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

Right now the repo has the architecture, preprocessing, class schema, split tooling, and eval script, but not the actual checkpoints/evaluation package. Without these, we can’t validate or freeze original Model 1.

Can you send the package or tell us where it is stored by Sep 1, 2026, 17:00 Europe/Istanbul? If we can’t recover it by then, we’ll keep original Model 1 blocked/not frozen and move to model1_baseline_v2.
```

## Requested Package

- `models/oceansense_domain_efficientnet_b0.pt`
- `models/oceansense_condition_efficientnet_b0.pt`
- approved image manifest or dataset folder
- real `labels.csv`
- immutable train/validation/test split
- evaluation configuration
- metrics output
- predictions and failure examples
- dataset license/access proof

## Follow-Up Rules

1. On any response, record the response time, exact response or safe summary, and whether a package location was provided.
2. Do not mark either checkpoint recovered until the exact file is received and validated against the Model 1 loading contract.
3. Record hashes and provenance for every received file before evaluation.
4. If there is no response by 2026-08-28 17:00 Europe/Istanbul, send one concise follow-up through the same channel.
5. If the complete valid package is not recovered by 2026-09-01 17:00 Europe/Istanbul, keep original Model 1 **BLOCKED / NOT FROZEN** and use the separately gated `model1_baseline_v2` fallback path.

## Integrity Statement

No checkpoint or other package file had been received when this log was created. No checkpoint is marked recovered, no Model 1 freeze is claimed, and no training was performed.
