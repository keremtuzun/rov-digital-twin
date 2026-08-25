"""Legacy pre-v0 structural-temporal scoring heuristic.

This is an R&D prototype, not a trained detector and not a validated proprietary claim.
Model 1 supplies observations; this mechanism reasons about persistence, viewpoint,
uncertainty, and relationships between inspected components.

It is not the dynamic Model 2 v0 architecture and is retained only as historical,
transparent research code until the required baselines are implemented.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


COMPONENT_TYPES = {"pipe", "weld", "joint", "coating", "hull", "cable", "support", "concrete"}
RELATION_TYPES = {"weld_connects", "joint_connects", "coating_on", "adjacent_to", "part_of"}


@dataclass(frozen=True)
class EvidenceObservation:
    frame_id: str
    target_id: str
    timestamp: float
    component_type: str
    condition_label: str
    concern_score: float
    uncertainty: float
    viewpoint_angle_deg: float
    distance_m: float
    evidence_ref: str

    def __post_init__(self) -> None:
        if not self.frame_id.strip() or not self.target_id.strip() or not self.evidence_ref.strip():
            raise ValueError("frame_id, target_id and evidence_ref are required")
        if self.component_type not in COMPONENT_TYPES:
            raise ValueError(f"unsupported component_type: {self.component_type}")
        if not 0 <= self.concern_score <= 1 or not 0 <= self.uncertainty <= 1:
            raise ValueError("concern_score and uncertainty must be between 0 and 1")
        if not 0 <= self.viewpoint_angle_deg <= 90 or self.distance_m <= 0:
            raise ValueError("viewpoint angle or distance is outside the supported range")


@dataclass(frozen=True)
class StructuralRelation:
    source_target_id: str
    destination_target_id: str
    relation_type: str

    def __post_init__(self) -> None:
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(f"unsupported relation_type: {self.relation_type}")
        if self.source_target_id == self.destination_target_id:
            raise ValueError("a structural relation must connect distinct targets")


@dataclass(frozen=True)
class StructuredConditionState:
    prototype_version: str
    target_id: str
    component_type: str
    condition_hypothesis: str
    risk_score: float
    confidence: float
    unknown: bool
    frame_count: int
    persistence: float
    viewpoint_coverage: float
    relationship_support: float
    evidence_refs: list[str]
    mechanism_trace: dict[str, Any]
    recommended_decision: str
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StructuralTemporalReasoner:
    """Aggregate Model 1 evidence with falsifiable structural/temporal mechanisms."""

    VERSION = "model2_structural_temporal_hypothesis_v0.1"

    def __init__(self, *, enable_temporal: bool = True, enable_structure: bool = True,
                 enable_viewpoint: bool = True, minimum_frames: int = 3) -> None:
        if minimum_frames < 1:
            raise ValueError("minimum_frames must be positive")
        self.enable_temporal = enable_temporal
        self.enable_structure = enable_structure
        self.enable_viewpoint = enable_viewpoint
        self.minimum_frames = minimum_frames

    @staticmethod
    def _viewpoint_weight(observation: EvidenceObservation) -> float:
        angle = max(0.0, math.cos(math.radians(observation.viewpoint_angle_deg)))
        distance = math.exp(-abs(observation.distance_m - 1.0) / 2.0)
        return max(0.05, angle * distance)

    def reason(self, target_id: str, observations: Iterable[EvidenceObservation],
               relations: Iterable[StructuralRelation] = ()) -> StructuredConditionState:
        all_observations = list(observations)
        target = sorted(
            (item for item in all_observations if item.target_id == target_id),
            key=lambda item: (item.timestamp, item.frame_id),
        )
        if not target:
            raise ValueError(f"no observations for target_id={target_id}")
        weights = [
            (self._viewpoint_weight(item) if self.enable_viewpoint else 1.0)
            * (1.0 - item.uncertainty)
            for item in target
        ]
        total_weight = sum(weights)
        evidence_score = (
            sum(item.concern_score * weight for item, weight in zip(target, weights)) / total_weight
            if total_weight > 0 else 0.0
        )
        positive_frames = sum(item.concern_score >= 0.55 for item in target)
        persistence = positive_frames / len(target) if self.enable_temporal else 0.0
        angles = [item.viewpoint_angle_deg for item in target]
        viewpoint_coverage = min(1.0, (max(angles) - min(angles)) / 45.0) if len(angles) > 1 else 0.0

        relation_list = list(relations)
        neighbor_ids = {
            relation.destination_target_id if relation.source_target_id == target_id
            else relation.source_target_id
            for relation in relation_list
            if target_id in {relation.source_target_id, relation.destination_target_id}
        }
        neighbor_support = [
            item.concern_score * (1.0 - item.uncertainty)
            for item in all_observations if item.target_id in neighbor_ids
        ]
        relationship_support = (
            sum(neighbor_support) / len(neighbor_support)
            if self.enable_structure and neighbor_support else 0.0
        )
        temporal_term = 0.20 * persistence if self.enable_temporal else 0.0
        structural_term = 0.15 * relationship_support if self.enable_structure else 0.0
        risk = min(1.0, 0.65 * evidence_score + temporal_term + structural_term)
        mean_uncertainty = sum(item.uncertainty for item in target) / len(target)
        enough_frames = len(target) >= self.minimum_frames if self.enable_temporal else True
        evidence_diverse = viewpoint_coverage >= 0.15 or len(target) >= self.minimum_frames + 1
        viewpoint_confidence = 0.20 * viewpoint_coverage if self.enable_viewpoint else 0.0
        confidence = min(1.0, (1.0 - mean_uncertainty)
                         * (0.55 + 0.25 * persistence + viewpoint_confidence))
        unknown = not enough_frames or not evidence_diverse or confidence < 0.45
        condition = max(target, key=lambda item: item.concern_score).condition_label
        if unknown:
            decision = "request_reinspection"
        elif risk >= 0.75:
            decision = "escalate"
        elif risk >= 0.45:
            decision = "accept_detection"
        else:
            decision = "flag_unknown" if mean_uncertainty > 0.45 else "accept_detection"
        return StructuredConditionState(
            prototype_version=self.VERSION,
            target_id=target_id,
            component_type=target[0].component_type,
            condition_hypothesis=condition,
            risk_score=round(risk, 6),
            confidence=round(confidence, 6),
            unknown=unknown,
            frame_count=len(target),
            persistence=round(persistence, 6),
            viewpoint_coverage=round(viewpoint_coverage, 6),
            relationship_support=round(relationship_support, 6),
            evidence_refs=sorted({item.evidence_ref for item in target}),
            mechanism_trace={
                "evidence_score": round(evidence_score, 6),
                "temporal_term": round(temporal_term, 6),
                "structural_term": round(structural_term, 6),
                "enable_temporal": self.enable_temporal,
                "enable_structure": self.enable_structure,
                "enable_viewpoint": self.enable_viewpoint,
                "minimum_frames": self.minimum_frames,
            },
            recommended_decision=decision,
            limitations=[
                "Research hypothesis only; thresholds are not calibrated on field inspection outcomes.",
                "Input scores inherit Model 1 dataset and labeling limitations.",
                "Structural relations are supplied metadata, not independently verified geometry.",
            ],
        )


def run_ablation(target_id: str, observations: Iterable[EvidenceObservation],
                 relations: Iterable[StructuralRelation]) -> dict[str, dict[str, Any]]:
    observations, relations = list(observations), list(relations)
    variants = {
        "full": StructuralTemporalReasoner(),
        "without_temporal": StructuralTemporalReasoner(enable_temporal=False),
        "without_structure": StructuralTemporalReasoner(enable_structure=False),
        "model1_score_only": StructuralTemporalReasoner(
            enable_temporal=False, enable_structure=False, enable_viewpoint=False,
        ),
    }
    return {
        name: reasoner.reason(target_id, observations, relations).to_dict()
        for name, reasoner in variants.items()
    }
