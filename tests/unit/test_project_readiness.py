import json
from pathlib import Path


def test_readiness_distinguishes_training_completion_from_deployment():
    root = Path(__file__).resolve().parents[2]
    status = json.loads((root / "docs/PROJECT_READINESS.json").read_text())
    assert status["research_training_status"] == "COMPLETE_BOUNDED_LOCAL_SEARCH"
    assert not status["blocked_due_to_missing_training_resources"]
    assert status["current_gate"] == "WAITING_FOR_REPRESENTATIVE_PHYSICAL_DATA_AND_STAGED_VALIDATION"
    assert not status["physical_validation_complete"]
    assert not status["deployment_authorized"]
    assert not status["physical_data_is_proven_only_possible_improvement"]
