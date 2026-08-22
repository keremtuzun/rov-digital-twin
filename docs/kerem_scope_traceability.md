# Kerem scope traceability

| Build-plan requirement | Implementation | Verification / status |
|---|---|---|
| Image/frame input | `PerceptionService.analyze` | Integration test uses a real filesystem frame path |
| Seven cautious labels | `schemas.ALLOWED_LABELS`, `config/labels.yaml` | Invalid/unsafe labels raise errors |
| Dataset CSV and boxes | `oceansense.data`, examples under `dataset/` | Schema, file, ID, label, and box validation tests |
| Train/val/test split | `scripts/split_image_dataset.py` | Deterministic stratified split test |
| EfficientNet-B0 | `scripts/train_classifier.py`, inference adapter | Training requires a license-reviewed image snapshot |
| YOLOv8n weak-point boxes | `scripts/train_detector.py`, optional adapter | Deliberately optional until real boxes exist |
| Anomaly score | `oceansense.anomaly.score_anomaly` | Boundary behavior tested |
| RAG / specialized explanation | `GroundedExplainer`, packaged knowledge base | Retrieval sources returned; language is caution-gated |
| Rule-based decision agent | `DecisionAgent` | All six required scenarios tested |
| Perception + decision APIs | `oceansense.api` | Both POST contracts tested with FastAPI TestClient |
| Structured demo JSON | `outputs/demo_json/` | JSON parse and contract covered by core types |
| Evaluation output | `scripts/train_classifier.py`, `scripts/train_detector.py` | Generates metrics only after real training; no fabricated report |
| Burak integration | `docs/integration_guide.md` | High-level intent only; no motor/thruster output |

## Deliberate limitations

No public imagery or trained checkpoint is committed because the project has not yet selected and
recorded a license-reviewed dataset snapshot. SUIM and URPC license scope needs clarification; TrashCan
has source-footage restrictions; Brackish is useful for underwater domain examples but not structural
damage. The code therefore makes no crack, corrosion, weak-material, or real-world deployment claim.
