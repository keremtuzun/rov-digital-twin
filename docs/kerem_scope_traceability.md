# Kerem scope traceability

| Build-plan requirement | Implementation | Verification / status |
|---|---|---|
| Image/frame input | `PerceptionService.analyze` | Integration test uses a real filesystem frame path |
| Six inspection domains + cautious conditions | `DOMAIN_LABELS`, `CONDITION_LABELS`, `config/labels.yaml` | Invalid domains/conditions raise errors |
| Dataset CSV and boxes | `oceansense.data`, examples and ImageFolder preparation | Domain, condition, origin, file, ID, label, and box validation tests |
| Train/val/test split | `scripts/split_image_dataset.py` | Deterministic stratified split test |
| Domain + condition classifiers | two EfficientNet-B0 entry points and inference adapters | Training requires a license-reviewed multi-domain snapshot |
| YOLOv8n weak-point boxes | `scripts/train_detector.py`, optional adapter | Deliberately optional until real boxes exist |
| Domain-aware condition/risk score | `oceansense.scoring.assess_condition` | Status, score, risk, and fishing field assessment are structured |
| RAG / specialized explanation | `GroundedExplainer`, packaged knowledge base | Retrieval sources returned; language is caution-gated |
| Rule-based decision agent | `DecisionAgent` | All 11 documented domain/safety scenarios tested |
| Perception + decision APIs | `oceansense.api` | Both POST contracts tested with FastAPI TestClient |
| Structured demo JSON | `outputs/demo_json/` | JSON parse and contract covered by core types |
| Evaluation output | classifier/detector trainers and `evaluate_multidomain.py` | Per-class and per-domain metrics only after real training; no fabricated report |
| Burak integration | `docs/integration_guide.md` | High-level intent only; no motor/thruster output |

## Deliberate limitations

No public imagery or trained checkpoint is committed because the project has not yet selected and
recorded a license-reviewed dataset snapshot. SUIM and URPC license scope needs clarification; TrashCan
has source-footage restrictions; Brackish is useful for underwater domain examples but not structural
damage. The code therefore makes no crack, corrosion, weak-material, or real-world deployment claim.
