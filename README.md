# OceanSense / ROV Digital Twin Intelligence Stack

This repository is the software-first Conrad/OceanSense inspection stack. The current phase proves
data discipline, repeatable evaluation, simulation interfaces and evidence-bounded inspection
reasoning without requiring a physical robot. Hardware construction and claims of physical deployment
are explicitly deferred until the staged validation gates are satisfied.

The software is organized around four distinct pillars:

1. **Model 1** - a conventional underwater visual-inspection baseline. Its code exists and the openly
   licensed SeaClear source has been acquired/hash-inventoried, but full-schema human-reviewed labels,
   an immutable split, and approved checkpoints do not; Model 1 v1 freeze is therefore blocked rather
   than fabricated.
2. **Navigation digital twin** - Unity robot motion, thrusters, hydrodynamics, sensors, missions and
   PPO research. It simulates the robot and viewpoint context, not structural damage truth.
3. **Failure Twin / inspection research environment** - a graph-based hidden degradation simulator with
   partial/noisy observations for Model 2. The older seeded 2D image-pair generator remains a separate
   visual fixture for interface demos; neither simulator claims calibrated physical truth.
4. **Model 2 research** - a non-traditional structural-temporal reasoning hypothesis that consumes
   Model 1 observations, viewpoint history, uncertainty and structural relations. It includes explicit
   score-only/temporal/structural ablations and is not presented as a validated proprietary invention.

The current standalone Model 2 track now begins one level earlier: `oceansense.model2` generates
connected structural graphs, simulator-only degradation trajectories and partial/noisy masked
Model-1-like observations. This is an experimental environment, not a second image detector.
All six conventional S1 comparators are now implemented and evaluated: Last Observation,
Simple Heuristic, Independent MLP, Temporal GRU, Static GNN and Temporal GNN. The custom
Model 2 remains a separate research gate, not another name for these baselines.
See `docs/CONRAD_DEVELOPMENT_STATUS_2026_09_04.md` for the current verified state.

The target software-first demonstration chain is:

```text
recorded/simulated navigation event -> frame + pose + target context
  -> frozen Model 1 observation -> failure analysis / dataset gaps
  -> optional Model 2 structural-temporal reasoning + ablations
  -> evidence-only mission decision -> accept / reinspect / change viewpoint / unknown / escalate
```

The repository does **not** claim a frozen underwater Model 1: no license-reviewed image snapshot or
approved checkpoint is committed. The telemetry weak-point classifier is a vehicle-health baseline,
not Model 1. The repository includes a 250,081-step experimental hybrid PPO waypoint policy and a trained
synthetic-telemetry weak-point classifier. A historical frozen high-difficulty simulation evaluation
recorded success 1.0 in all 24 reporting windows and no flip event across 59,919 steps. Subsequent
actuator/environment changes make that ONNX artifact a legacy-dynamics baseline, not a validation of
the current simulator. Neither model is approved for real-vehicle control; metrics, limitations and
promotion gates are versioned with the artifacts.

## Execution-guide workflows

Generate the fixed Model 2 Failure Twin v0 debug dataset without training a model:

```powershell
python -m pip install -e ".[model2]"
python scripts/generate_model2_dataset.py --config configs/model2/twin_v0.yaml `
  --output data/simulated/model2_debug_v0
python scripts/visualize_model2_scenario.py data/simulated/model2_debug_v0/scenario_000000 `
  --output outputs/model2_debug_plots
```

Run the navigation-plus-visual-fixture interface demo without Unity or physical hardware. This is not
a Model 2 or Failure Twin v0 validation command:

```powershell
python -m pip install -e ".[vision]"
python scripts/run_digital_twin_demo.py --run-id digital-twin-demo-v1
```

This command separately runs the controlled 2D visual fixture and deterministic navigation replay, links
`mission_id`, `frame_id`, `target_id`, `scenario_id` and `run_id`, invokes an explicitly non-model
placeholder because Model 1 is not frozen, produces a safe `flag_unknown` decision, and writes a run
manifest plus JSON/Markdown reports under `experiments/runs/<run_id>/`.

Generate 100 reproducible failure-twin pairs with masks and metadata:

```powershell
python -m pip install -e ".[vision]"
python scripts/run_failure_twin_batch.py --config config/failure_twin_mvp.json `
  --output outputs/failure_twin_mvp
```

Run the Model 2 structural-temporal hypothesis and required ablations:

```powershell
python scripts/run_model2_experiment.py inputs/model2_evidence.json --target-id pipe_01 `
  --output outputs/model2_ablation.json
```

Validate shared prediction records and export metrics/failures:

```powershell
python scripts/evaluate_predictions.py outputs/predictions.jsonl `
  --metrics outputs/metrics.json --failure-index outputs/failure_index.csv
python scripts/generate_report.py experiments/run_manifest.json --output outputs/run_report.md
```

See `docs/master_execution_alignment.md`, `docs/claim_boundaries.md`,
`docs/model1_freeze_report.md`, `docs/failure_twin_spec.md` and
`docs/model2_research_log.md` for current evidence boundaries and next gates.

## Navigation digital twin quick start

Open the `unity` folder with Unity 6. The project restores ML-Agents and ROS-TCP-Connector, then
automatically generates the `OceanSenseDemo` scene and editable ROV prefab. Runtime navigation is explicitly
`HeuristicOnly` until a policy is retrained and qualified on the current plant model. See `unity/README.md` for
controls, API/ROS startup and architecture, and `docs/unity_training_operations.md` for reproducible
staged training and the sim-to-real validation process.

Research-prototype controls include a versioned Unity/ROS/Python telemetry contract, license-gated
asset manifests, mission/video-safe splitting, cautious canonical labels, calibration/safety metrics,
synthetic capture metadata and staged Unity/HIL acceptance. Start with `docs/gap_analysis.md` and
`docs/dataset_acquisition_plan.md` and `docs/rl_policy_model_card.md`. The committed RL checkpoint has
historical simulation evidence but requires requalification on the current simulator; approved image
checkpoints remain absent.

## OceanSense quick start

```powershell
python -m pip install -e ".[api]"
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python scripts/run_api.py
```

The new Model 1 fallback remains fail-closed. Check its data/authorization gate with:

```powershell
python scripts/preflight_model1_baseline_v2.py --config configs/model1_baseline_v2.yaml
```

Only after this command reports `ready: true` may the separately versioned v2 training commands in
`docs/MODEL1_BASELINE_V2_FALLBACK_PLAN.md` be used. The older original-model commands below are retained as
historical/recovery reference and must not be used to fabricate the missing v1 package:

```powershell
python -m pip install -e ".[vision]"
python scripts/validate_image_dataset.py dataset/processed/labels.csv --boxes dataset/annotations/bboxes.json
python scripts/prepare_imagefolders.py --labels dataset/processed/labels.csv
python scripts/train_domain_classifier.py --data dataset/imagefolders/domain
python scripts/train_condition_classifier.py --data dataset/imagefolders/condition
python scripts/evaluate_multidomain.py --labels dataset/processed/labels.csv `
  --domain-checkpoint models/oceansense_domain_efficientnet_b0.pt `
  --condition-checkpoint models/oceansense_condition_efficientnet_b0.pt
```

See `docs/data_sources.md`, `docs/dataset_card.md`, `docs/model_card.md`, `docs/agent_card.md`, and
`docs/integration_guide.md` before integrating or making performance claims.

Bu depo; Unity tabanli bir su alti robotu dijital ikizi icin veri uretimi, zayif-nokta (weak point) siniflandirmasi, alan-uzman LLM hazirligi ve emniyet-kapili karar ajanini tek bir referans mimaride birlestirir.

## Neler calisiyor?

- Deterministik sentetik telemetri veri uretimi (normal + 4 ariza sinifi)
- Saf Python softmax siniflandirici egitimi, model serilestirme ve metrik raporu
- Tek kayit veya CSV uzerinden weak-point tahmini
- Risk, kural ve alan bilgisi birlestiren karar ajani
- LLM instruction veri seti uretimi ve opsiyonel LoRA fine-tuning giris noktasi
- Unity C# hidrodinamik, duty ve ML-Agents ornekleri
- ROS 2 telemetri/komut koprusu icin referans node
- Unit ve uctan uca testler
- Turkce proje outline dokumani (`docs/ROV_Digital_Twin_Project_Outline.docx`)

## Hizli baslangic

Kurulum gerektirmeyen demo (Python 3.10+):

```powershell
$env:PYTHONPATH = "src"
python -m rov_dt.cli demo --output-dir artifacts/demo
```

Adim adim:

```powershell
$env:PYTHONPATH = "src"
python -m rov_dt.cli generate --rows 4000 --output data/telemetry.csv
python -m rov_dt.cli train --input data/telemetry.csv --model models/weakpoint.json --report artifacts/metrics.json
python -m rov_dt.cli decide --model models/weakpoint.json --input data/telemetry.csv --row 12
python -m rov_dt.cli build-llm-data --input data/telemetry.csv --output data/llm_instructions.jsonl
```

Testler:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Mimari

```text
Unity / ROS 2 telemetry
        |
        v
schema validation -> feature vector -> weak-point classifier
                                           |
                                           v
domain advisor (LLM/RAG-ready) -> safety decision agent -> action + rationale
                                           |
                                           v
                              operator / ROS command gateway
```

Karar ajani dogrudan motor komutu vermek yerine varsayilan olarak `operator_review`, `degraded_mode` veya `abort_and_surface` gibi emniyetli niyetler uretir. Gercek araca komut gonderimi, ayrica yetkilendirilmis bir ROS gateway ve donanim-in-the-loop test kapisi gerektirir.

## Dizinler

- `src/rov_dt/`: veri, model, LLM verisi ve karar mantigi
- `unity/Assets/ROVDigitalTwin/Scripts/`: Unity/ML-Agents referans kodu
- `ros2/rov_dt_bridge/`: ROS 2 kopru node'u
- `configs/`: ML-Agents ve LoRA konfigürasyonlari
- `knowledge/`: alan-uzman LLM bilgi tabani
- `docs/`: proje outline ve mimari dokumani
- `tests/`: deterministik testler

## Uretime gecis kapilari

Bu depo bir referans/MVP'dir; sentetik veri gercek ariza verisinin yerine gecmez. Uretimden once sensör zaman senkronizasyonu, gercek ROV kalibrasyonu, HIL/SIL testleri, fail-safe durum makinesi, model drift izleme ve operator onayi zorunlu tutulmalidir.

## Reliability and sim-to-real architecture

```text
Unity synthetic telemetry / canonical real mission export (schema 2.0.0)
  -> validation + missing masks + provenance + data-quality monitor
  -> causal temporal features + physics residuals + model ensemble
  -> calibration + OOD/uncertainty + deterministic sensor-health monitor
  -> failure-first decision rules -> allowlisted high-level intent -> deterministic flight controller
```

The legacy `1.0.0` Unity contract remains supported. New pool/lake/sea missions use the `2.0.0`
envelope and explicitly distinguish `simulated`, `measured`, `derived` and unavailable fields. Load CSV,
canonical JSONL or an explicit ROS-bag export with `rov_dt.real_data`; missing measurements remain `None`
and have a false mask. Native bag topics must be mapped explicitly—loaders never guess topic semantics.

Deployment modes are `simulation`, `shadow`, `advisory` and explicitly enabled
`autonomous_high_level`. Shadow is the real-world validation default: predictions are versioned and
logged but cannot affect vehicle behavior. No diagnostic, perception, classifier or LLM output may
contain PWM, motor voltage/torque or individual thruster force.

Replay a canonical mission deterministically:

```powershell
python scripts/replay_mission.py mission.jsonl --model models/weakpoint_v2.json --output outputs/replay.json
```

Fit only identifiable simulator parameters, leaving unavailable values null:

```powershell
python scripts/identify_vehicle_parameters.py mission.jsonl --vehicle-id rov_001 `
  --output vehicle_profiles/rov_001-v1.json
```

Retraining follows mission-disjoint `train -> validation/calibration -> test`. Temporal windows are
past-only, temperature scaling is fitted on validation data, and test conditions are reported separately.
Use `config/domain_randomization.yaml` and `config/unity_ppo_curriculum_v2.yaml` to progress from calm
water to combined disturbances. See `docs/hil_architecture.md` and `docs/validation_plan.md` before any
energized or wet test. The project remains experimental until every applicable stage is signed off.
