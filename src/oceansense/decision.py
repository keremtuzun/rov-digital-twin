from __future__ import annotations

from itertools import count

from .rag import GroundedExplainer
from .schemas import DecisionResult, MissionContext, PerceptionResult


class DecisionAgent:
    """Rule-based safety authority; the explainer never selects or overrides actions."""

    def __init__(self, explainer: GroundedExplainer) -> None:
        self.explainer = explainer
        self._ids = count(1)

    def decide(self, perception: PerceptionResult, context: MissionContext) -> DecisionResult:
        confidence = perception.classification.confidence
        label = perception.classification.label
        flags: list[str] = []
        review = False

        if context.battery_level is not None and context.battery_level < 0.20:
            action, priority, reason = "return_to_base", "critical", "Battery is below the 20% safety threshold."
            flags.append("low_battery")
            review = True
        elif context.communication_status in {"unstable", "lost"}:
            action, priority, reason = "hold_position", "critical", "Communication is not stable."
            flags.append("communication_unstable")
            review = True
        elif context.visibility_level == "poor":
            action, priority, reason = "capture_more_data", "high", "Visibility is poor; collect better evidence."
            flags.append("poor_visibility")
            review = True
        elif confidence < 0.50 or label == "unknown":
            action, priority, reason = "request_human_review", "high", "Model confidence is insufficient for an automated recommendation."
            flags.append("low_confidence")
            review = True
        elif perception.anomaly.level == "high" and confidence > 0.70:
            action, priority, reason = "inspect_closer", "high", "A high anomaly score requires closer inspection."
            flags.append("high_anomaly")
            review = True
        elif label == "normal_surface" and confidence > 0.75:
            action, priority, reason = "continue_survey", "normal", "Normal surface prediction exceeds the continuation threshold."
        else:
            action, priority, reason = "request_human_review", "medium", "The result falls between validated automatic decision thresholds."
            flags.append("ambiguous_result")
            review = True

        instruction = self._instruction(action)
        explanation = self.explainer.explain(perception, action)
        return DecisionResult(
            decision_id=f"DEC-{next(self._ids):05d}",
            frame_id=perception.frame_id,
            recommended_action=action,
            priority=priority,
            requires_human_review=review,
            reasoning_summary=reason,
            dashboard_message=self._dashboard(action, label),
            control_instruction=instruction,
            confidence="high" if confidence >= 0.75 else ("medium" if confidence >= 0.50 else "low"),
            safety_flags=flags,
            explanation=explanation,
        )

    @staticmethod
    def _instruction(action: str) -> dict:
        mapping = {
            "inspect_closer": {"action": "move_to_inspection_pose", "target": "detected_region", "suggested_distance_m": 0.7, "speed": "slow"},
            "continue_survey": {"action": "continue_current_survey_plan"},
            "capture_more_data": {"action": "capture_additional_frames", "speed": "slow"},
            "hold_position": {"action": "request_station_keeping"},
            "return_to_base": {"action": "request_return_to_base"},
            "request_human_review": {"action": "pause_high_level_progression"},
        }
        return mapping[action]

    @staticmethod
    def _dashboard(action: str, label: str) -> str:
        display_label = label.removeprefix("possible_").replace("_", " ")
        messages = {
            "inspect_closer": f"Possible {display_label} detected. Recommend closer inspection.",
            "continue_survey": "No high-confidence anomaly detected. Continue survey.",
            "capture_more_data": "Poor visibility. Capture more data before proceeding.",
            "hold_position": "Communication unstable. Hold position and notify operator.",
            "return_to_base": "Low battery. Recommend return to base.",
            "request_human_review": "Result is uncertain. Human review required.",
        }
        return messages[action]
