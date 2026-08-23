# Unified project traceability

| Build-plan requirement | Implementation | Verification / status |
|---|---|---|
| Image/frame input | `PerceptionService.analyze`, Unity inspection camera | API contract tests and local frame capture |
| Six inspection domains + cautious conditions | `DOMAIN_LABELS`, `CONDITION_LABELS`, `config/labels.yaml` | Invalid domains/conditions raise errors |
| Dataset CSV and boxes | `oceansense.data`, examples and ImageFolder preparation | Schema and split tests |
| Domain + condition classifiers | EfficientNet-B0 entry points and inference adapters | Ready; training intentionally not run |
| YOLOv8n weak-point boxes | `scripts/train_detector.py`, optional adapter | Ready; requires reviewed real boxes |
| Domain-aware condition/risk score | `oceansense.scoring.assess_condition` | Structured status, score and risk |
| Specialized grounded explanation | `GroundedExplainer`, packaged knowledge base | Retrieval sources returned; caution gated |
| Rule-based decision agent | `DecisionAgent` | Documented safety scenarios tested |
| Procedural underwater environment and robot | `CompleteProjectBuilder` | Static validation; Unity first-open verification required |
| Six-DOF hydrodynamics and current | `Hydrodynamics6Dof`, `WaterCurrentField` | Drag unit tests supplied |
| DVL, IMU, depth and sonar | Unity sensor components | Wired into 39 ML-Agents observations |
| Eight-thruster action interface | `ROVVehicle`, `Thruster`, `ROVRLAgent` | Eight continuous actions configured |
| Three duties | station keeping, pipeline tracking, waypoint | Duty manager, rewards and safety bounds |
| Operator UI and perception/decision link | dashboard, capture and API client | Generated into demo scene |
| ROS 2 integration | Unity UDP telemetry + `unity_udp_bridge` | High-level intent only; no raw actuator gateway |

## Deliberate limitations

No trained checkpoint is claimed or produced. The real imagery snapshot still requires source/license
review, and the generated Unity scene still requires Unity Editor compilation, Play Mode, SIL and HIL
validation before training or real-vehicle use.
