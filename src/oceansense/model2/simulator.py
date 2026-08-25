"""Failure Twin v0: structural graph, hidden dynamics, and Model-1-like observations."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

import networkx as nx
import numpy as np

from .schemas import (
    NODE_TYPES,
    OBSERVATION_FIELDS,
    STATE_FIELDS,
    STRUCTURE_TYPES,
    InspectionObservation,
    StructuralGraph,
    StructuralNode,
)


@dataclass(frozen=True)
class TwinConfig:
    n_nodes: int = 20
    timesteps: int = 10
    structure_types: tuple[str, ...] = tuple(sorted(STRUCTURE_TYPES))
    observation_coverage: float = 0.5
    intrinsic_degradation: float = 0.012
    noise_std: float = 0.01
    neighbor_coupling: float = 0.15
    environment_effect_weight: float = 0.01
    environment_level: float = 0.5
    false_positive_rate: float = 0.04
    false_negative_rate: float = 0.08
    severity_noise_std: float = 0.08
    confidence_noise_std: float = 0.05
    clip_range: tuple[float, float] = (0.0, 1.0)
    condition_weights: tuple[float, float, float, float] = (0.3, 0.3, 0.25, 0.15)
    component_type_overrides: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 10 <= self.n_nodes <= 100 or self.timesteps < 2:
            raise ValueError("Failure Twin v0 requires 10-100 nodes and at least two timesteps")
        if not self.structure_types or any(item not in STRUCTURE_TYPES for item in self.structure_types):
            raise ValueError("structure_types contains an unsupported value")
        for name in (
            "observation_coverage", "false_positive_rate", "false_negative_rate",
            "environment_level",
        ):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.noise_std < 0 or self.severity_noise_std < 0 or self.confidence_noise_std < 0:
            raise ValueError("noise values cannot be negative")
        if self.neighbor_coupling < 0 or self.environment_effect_weight < 0:
            raise ValueError("dynamics weights cannot be negative")
        if len(self.condition_weights) != 4 or not np.isclose(sum(self.condition_weights), 1.0):
            raise ValueError("condition_weights must contain four values summing to 1")
        if self.clip_range[0] >= self.clip_range[1]:
            raise ValueError("clip_range must be increasing")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> TwinConfig:
        source = dict(payload)
        source["structure_types"] = tuple(source.get("structure_types", sorted(STRUCTURE_TYPES)))
        source["clip_range"] = tuple(source.get("clip_range", (0.0, 1.0)))
        source["condition_weights"] = tuple(
            source.get("condition_weights", (0.3, 0.3, 0.25, 0.15))
        )
        return cls(**source)


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    graph: StructuralGraph
    config: TwinConfig
    states: np.ndarray
    observations: tuple[InspectionObservation, ...]
    observation_tensor: np.ndarray
    observation_mask: np.ndarray
    seed: int


def generate_structure(n_nodes: int, structure_type: str, seed: int) -> StructuralGraph:
    """Generate a connected structural graph using NetworkX."""
    if not 10 <= n_nodes <= 100:
        raise ValueError("n_nodes must be between 10 and 100")
    if structure_type not in STRUCTURE_TYPES:
        raise ValueError(f"unsupported structure type: {structure_type}")
    rng = random.Random(seed)
    if structure_type == "chain":
        nx_graph = nx.path_graph(n_nodes)
    elif structure_type == "branched_pipeline":
        nx_graph = nx.random_labeled_tree(n_nodes, seed=seed)
    elif structure_type == "small_lattice":
        nx_graph = nx.path_graph(n_nodes)
        for index in range(n_nodes - 2):
            if index % 3 == 0:
                nx_graph.add_edge(index, index + 2)
    else:
        nx_graph = nx.path_graph(n_nodes)
        candidates = [(a, b) for a in range(n_nodes) for b in range(a + 2, n_nodes)]
        rng.shuffle(candidates)
        for left, right in candidates[: max(1, n_nodes // 4)]:
            nx_graph.add_edge(left, right)
    node_type_pool = sorted(NODE_TYPES)
    nodes = tuple(
        StructuralNode(
            component_id=f"component_{index:03d}",
            node_type=node_type_pool[rng.randrange(len(node_type_pool))],
            criticality=round(rng.uniform(0.2, 1.0), 6),
            metadata={"index": index},
        )
        for index in range(n_nodes)
    )
    node_ids = [node.component_id for node in nodes]
    edges = tuple((node_ids[left], node_ids[right]) for left, right in nx_graph.edges())
    return StructuralGraph(
        nodes=nodes,
        edges=edges,
        seed=seed,
        structure_type=structure_type,
        metadata={"connected": nx.is_connected(nx_graph)},
    )


def _initial_states(n_nodes: int, config: TwinConfig, rng: np.random.Generator) -> np.ndarray:
    severity = rng.choice(4, size=n_nodes, p=(0.70, 0.20, 0.08, 0.02))
    ranges = np.asarray(((0.0, 0.08), (0.08, 0.3), (0.3, 0.65), (0.65, 0.9)))
    states = np.zeros((n_nodes, len(STATE_FIELDS)), dtype=np.float32)
    for index, level in enumerate(severity):
        low, high = ranges[level]
        states[index, :4] = rng.uniform(low, high, size=4)
    states[:, 4] = states[:, :4] @ np.asarray(config.condition_weights)
    return states


def _adjacency(graph: StructuralGraph) -> list[list[int]]:
    lookup = {node.component_id: index for index, node in enumerate(graph.nodes)}
    neighbors = [[] for _ in graph.nodes]
    for left, right in graph.edges:
        left_index, right_index = lookup[left], lookup[right]
        neighbors[left_index].append(right_index)
        neighbors[right_index].append(left_index)
    return neighbors


def evolve_states(
    graph: StructuralGraph,
    config: TwinConfig,
    seed: int,
    initial_state: np.ndarray | None = None,
) -> np.ndarray:
    """Evolve simulator-only hidden degradation state over time."""
    rng = np.random.default_rng(seed)
    current = (
        np.asarray(initial_state, dtype=np.float32).copy()
        if initial_state is not None else _initial_states(len(graph.nodes), config, rng)
    )
    expected_shape = (len(graph.nodes), len(STATE_FIELDS))
    if current.shape != expected_shape:
        raise ValueError(f"initial_state must have shape {expected_shape}")
    states = np.zeros((config.timesteps, *expected_shape), dtype=np.float32)
    states[0] = current
    neighbors = _adjacency(graph)
    for timestep in range(1, config.timesteps):
        updated = current.copy()
        for node_index, node in enumerate(graph.nodes):
            neighbor_mean = (
                current[neighbors[node_index], :4].mean(axis=0)
                if neighbors[node_index] else np.zeros(4)
            )
            override = config.component_type_overrides.get(node.node_type, 1.0)
            delta = (
                config.intrinsic_degradation * override
                + config.environment_effect_weight * config.environment_level
                + config.neighbor_coupling * neighbor_mean
                + rng.normal(0.0, config.noise_std, size=4)
            )
            updated[node_index, :4] = np.clip(
                current[node_index, :4] + delta, *config.clip_range
            )
        updated[:, 4] = np.clip(
            updated[:, :4] @ np.asarray(config.condition_weights), *config.clip_range
        )
        states[timestep] = updated
        current = updated
    return states


def _simulate_observations(
    scenario_id: str,
    graph: StructuralGraph,
    states: np.ndarray,
    config: TwinConfig,
    seed: int,
) -> tuple[tuple[InspectionObservation, ...], np.ndarray, np.ndarray]:
    """Create masked noisy observations without exposing hidden-state fields."""
    rng = np.random.default_rng(seed)
    timesteps, n_nodes, _ = states.shape
    mask = rng.random((timesteps, n_nodes)) < config.observation_coverage
    tensor = np.zeros((timesteps, n_nodes, len(OBSERVATION_FIELDS)), dtype=np.float32)
    records: list[InspectionObservation] = []
    probability_names = ("corrosion", "crack", "material_loss", "fatigue")
    for timestep in range(timesteps):
        for node_index, node in enumerate(graph.nodes):
            observed = bool(mask[timestep, node_index])
            if observed:
                probabilities = np.clip(
                    states[timestep, node_index, :4]
                    + rng.normal(0.0, config.severity_noise_std, size=4), 0.0, 1.0
                )
                false_negative = rng.random(4) < config.false_negative_rate
                false_positive = rng.random(4) < config.false_positive_rate
                probabilities[false_negative] *= 0.25
                probabilities[false_positive] = np.maximum(
                    probabilities[false_positive], rng.uniform(0.35, 0.75, false_positive.sum())
                )
                severity = float(np.clip(
                    states[timestep, node_index, 4]
                    + rng.normal(0.0, config.severity_noise_std), 0.0, 1.0
                ))
                confidence = float(np.clip(
                    1.0 - abs(severity - states[timestep, node_index, 4])
                    + rng.normal(0.0, config.confidence_noise_std), 0.0, 1.0
                ))
                tensor[timestep, node_index] = np.concatenate(
                    (probabilities, (severity, confidence))
                )
                defect_probabilities = {
                    name: float(value) for name, value in zip(probability_names, probabilities)
                }
            else:
                severity, confidence = None, 0.0
                defect_probabilities = {name: None for name in probability_names}
            records.append(InspectionObservation(
                scenario_id=scenario_id,
                component_id=node.component_id,
                timestamp=timestep,
                node_type=node.node_type,
                observed=observed,
                observation_mask=int(observed),
                defect_probabilities=defect_probabilities,
                severity_estimate=severity,
                confidence=confidence,
                pose_viewpoint=None,
            ))
    return tuple(records), tensor, mask.astype(np.uint8)


@dataclass(frozen=True)
class Model1Simulator:
    """Produce contract-compatible noisy evidence without running or impersonating Model 1."""

    config: TwinConfig

    def simulate(
        self,
        scenario_id: str,
        graph: StructuralGraph,
        states: np.ndarray,
        seed: int,
    ) -> tuple[tuple[InspectionObservation, ...], np.ndarray, np.ndarray]:
        return _simulate_observations(
            scenario_id, graph, states, self.config, seed
        )


def generate_observations(
    scenario_id: str,
    graph: StructuralGraph,
    states: np.ndarray,
    config: TwinConfig,
    seed: int,
) -> tuple[tuple[InspectionObservation, ...], np.ndarray, np.ndarray]:
    """Compatibility function backed by the explicit Model1Simulator component."""
    return Model1Simulator(config).simulate(scenario_id, graph, states, seed)


def generate_scenario(scenario_id: str, config: TwinConfig, seed: int) -> ScenarioResult:
    rng = random.Random(seed)
    structure_type = rng.choice(config.structure_types)
    graph = generate_structure(config.n_nodes, structure_type, seed)
    states = evolve_states(graph, config, seed + 1)
    observations, tensor, mask = generate_observations(
        scenario_id, graph, states, config, seed + 2
    )
    return ScenarioResult(
        scenario_id=scenario_id,
        graph=graph,
        config=config,
        states=states,
        observations=observations,
        observation_tensor=tensor,
        observation_mask=mask,
        seed=seed,
    )


def config_to_dict(config: TwinConfig) -> dict[str, Any]:
    return asdict(config)
