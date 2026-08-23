# Reproducible training and evaluation protocol

## Before any long/GPU run

Run the license audit, class/source distribution, duplicate report and group split. Report approved row
count, estimated decoded disk use, GPU type and duration, then request approval. The default classifier
does not download ImageNet weights; `--weights imagenet` is an explicit network-enabled choice.

Image models use mission/video-separated train/validation/test data, deterministic seeds, optional
weighted loss/sampling, manifest/config hashes and checkpoint metadata. Reports include confusion,
per-class precision/recall/F1, macro F1, balanced accuracy, ECE, threshold coverage, safety false
negatives, and source/visibility/real-vs-synthetic breakdowns. Reports must separately call out:

- structural concern predicted as normal;
- marine debris predicted as normal;
- poor visibility predicted as normal;
- unknown predicted incorrectly above 0.8 confidence;
- degradation concentrated in one source.

Synthetic images never enter the real external test set. A synthetic result is not crack, corrosion,
chemical pollution or physical integrity evidence.

## Telemetry and RL

Telemetry split is by mission/session, not row. Fault scenarios are normal, thruster degradation,
sensor drift, buoyancy imbalance, added drag/tether obstruction, low battery, communication loss, DVL
dropout and combined faults. Future captures progress from SIL to pool/HIL/ROS bags with operator labels.

PPO does not train from a fixed image/telemetry dataset; it collects transitions through simulation
interaction. Before PPO, verify the 39-observation/8-action contract, reward decomposition and reset/
stop safety. A later approved experiment must record seed, curriculum, domain-randomization ranges,
success and collision rates, energy, safe-volume violations and held-out-scene generalization. No PPO
training is authorized by this document.
