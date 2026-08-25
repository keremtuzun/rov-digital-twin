"""Schemas that keep simulator-only truth separate from inference observations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


NODE_TYPES = {"pipe", "weld", "joint", "support", "beam", "connector", "valve"}
STRUCTURE_TYPES = {"chain", "branched_pipeline", "small_lattice", "mixed_structure"}
STATE_FIELDS = ("corrosion", "crack", "material_loss", "fatigue", "condition")
OBSERVATION_FIELDS = (
    "corrosion_probability",
    "crack_probability",
    "material_loss_probability",
    "fatigue_probability",
    "severity_estimate",
    "confidence",
)


@dataclass(frozen=True)
class StructuralNode:
    component_id: str
    node_type: str
    criticality: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.node_type not in NODE_TYPES:
            raise ValueError(f"unsupported node type: {self.node_type}")
        if not 0 <= self.criticality <= 1:
            raise ValueError("criticality must be between 0 and 1")


@dataclass(frozen=True)
class StructuralGraph:
    nodes: tuple[StructuralNode, ...]
    edges: tuple[tuple[str, str], ...]
    seed: int
    structure_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.structure_type not in STRUCTURE_TYPES:
            raise ValueError(f"unsupported structure type: {self.structure_type}")
        node_ids = {node.component_id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("component IDs must be unique")
        if any(left not in node_ids or right not in node_ids for left, right in self.edges):
            raise ValueError("every edge endpoint must reference a graph node")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [list(edge) for edge in self.edges],
            "seed": self.seed,
            "structure_type": self.structure_type,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class InspectionObservation:
    scenario_id: str
    component_id: str
    timestamp: int
    node_type: str
    observed: bool
    observation_mask: int
    defect_probabilities: dict[str, float | None]
    severity_estimate: float | None
    confidence: float
    source: str = "model1_simulator_v0"
    pose_viewpoint: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.node_type not in NODE_TYPES:
            raise ValueError(f"unsupported node type: {self.node_type}")
        if self.observation_mask not in (0, 1):
            raise ValueError("observation_mask must be binary")
        if self.observed != bool(self.observation_mask):
            raise ValueError("observed and observation_mask disagree")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.observed and (
            self.severity_estimate is not None
            or any(value is not None for value in self.defect_probabilities.values())
        ):
            raise ValueError("unobserved nodes cannot contain inferred values")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
