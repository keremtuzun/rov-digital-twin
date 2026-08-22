from __future__ import annotations

import json
from pathlib import Path

from oceansense.anomaly import score_anomaly
from oceansense.decision import DecisionAgent
from oceansense.rag import GroundedExplainer
from oceansense.schemas import Classification, InspectionDomain, MissionContext, PerceptionResult
from oceansense.scoring import assess_condition

SCENARIOS = [
    ("normal_structure", "structure", "structure_ok", 0.90, {}),
    ("structure_weak_point", "structure", "possible_weak_point", 0.84, {}),
    ("coral_stress", "nature_ecology", "possible_coral_stress", 0.78, {}),
    ("marine_debris", "contamination", "marine_debris", 0.82, {}),
    ("oil_like_sheen", "contamination", "oil_like_sheen", 0.76, {}),
    ("fish_activity", "fishing_aquaculture", "fish_or_habitat_activity", 0.79, {}),
    ("net_damage", "fishing_aquaculture", "net_damage", 0.74, {}),
    ("low_battery", "structure", "structure_ok", 0.90, {"battery_level": 0.15}),
]


def main() -> None:
    root = Path(__file__).parents[1]
    agent = DecisionAgent(GroundedExplainer(root / "src" / "oceansense" / "knowledge_base"))
    outputs = []
    for index, (name, domain_label, condition_label, confidence, context_overrides) in enumerate(SCENARIOS, 1):
        domain = InspectionDomain(domain_label, 0.88)
        classification = Classification(condition_label, confidence)
        perception = PerceptionResult(
            frame_id=f"demo_{index:03d}",
            classification=classification,
            anomaly=score_anomaly(classification),
            inspection_domain=domain,
            condition_assessment=assess_condition(domain, classification),
            model_version="documented_integration_fixture_v2",
        )
        context = MissionContext(survey_goal=domain_label, **context_overrides)
        outputs.append({
            "scenario": name,
            "fixture_notice": "Contract/safety fixture; not a trained-model prediction.",
            "perception": perception.to_dict(),
            "decision": agent.decide(perception, context).to_dict(),
        })
    destination = root / "outputs" / "demo_json" / "domain_scenarios.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
