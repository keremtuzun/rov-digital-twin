import json

import networkx as nx
import numpy as np

from oceansense.model2.dataset import generate_dataset
from oceansense.model2.schemas import STATE_FIELDS
from oceansense.model2.simulator import (
    TwinConfig,
    evolve_states,
    generate_scenario,
    generate_structure,
)
from oceansense.model2.visualization import visualize_scenario


def _nx_graph(structure):
    graph = nx.Graph()
    graph.add_nodes_from(node.component_id for node in structure.nodes)
    graph.add_edges_from(structure.edges)
    return graph


def test_generated_structures_are_connected_and_reproducible():
    for structure_type in ("chain", "branched_pipeline", "small_lattice", "mixed_structure"):
        first = generate_structure(20, structure_type, 42)
        second = generate_structure(20, structure_type, 42)
        assert first == second
        assert nx.is_connected(_nx_graph(first))


def test_hidden_states_evolve_stay_bounded_and_are_reproducible():
    config = TwinConfig(n_nodes=20, timesteps=10)
    first = generate_scenario("scenario-test", config, 101)
    second = generate_scenario("scenario-test", config, 101)
    assert np.array_equal(first.states, second.states)
    assert np.array_equal(first.observation_mask, second.observation_mask)
    assert np.array_equal(first.observation_tensor, second.observation_tensor)
    assert first.states.shape == (10, 20, len(STATE_FIELDS))
    assert np.all((first.states >= 0) & (first.states <= 1))
    assert not np.array_equal(first.states[0], first.states[-1])


def test_neighbor_coupling_changes_trajectories():
    graph = generate_structure(20, "chain", 7)
    initial = np.zeros((20, 5), dtype=np.float32)
    initial[0, :4] = 0.8
    initial[0, 4] = 0.8
    base = dict(
        n_nodes=20, timesteps=5, intrinsic_degradation=0.0,
        environment_effect_weight=0.0, noise_std=0.0,
    )
    uncoupled = evolve_states(graph, TwinConfig(**base, neighbor_coupling=0.0), 9, initial)
    coupled = evolve_states(graph, TwinConfig(**base, neighbor_coupling=0.3), 9, initial)
    assert np.array_equal(uncoupled[:, 1, :4], np.zeros((5, 4)))
    assert coupled[-1, 1, :4].mean() > 0


def test_observations_are_partial_noisy_and_do_not_leak_hidden_truth():
    result = generate_scenario(
        "scenario-observation", TwinConfig(observation_coverage=0.5), 808
    )
    assert np.any(result.observation_mask == 0)
    assert np.any(result.observation_mask == 1)
    observed = [record for record in result.observations if record.observed]
    hidden_lookup = {
        (timestep, index): result.states[timestep, index, 4]
        for timestep in range(result.states.shape[0])
        for index in range(result.states.shape[1])
    }
    node_lookup = {node.component_id: index for index, node in enumerate(result.graph.nodes)}
    assert any(
        not np.isclose(
            record.severity_estimate,
            hidden_lookup[(record.timestamp, node_lookup[record.component_id])],
        )
        for record in observed
    )
    forbidden = set(STATE_FIELDS) | {"hidden_state", "true_condition", "ground_truth"}
    for record in result.observations:
        assert forbidden.isdisjoint(record.to_dict())
        if not record.observed:
            assert record.severity_estimate is None
            assert all(value is None for value in record.defect_probabilities.values())


def test_dataset_uses_scenario_level_disjoint_splits_and_expected_shapes(tmp_path):
    config = {
        "dataset_version": "fixture-v0", "dataset_seed": 12, "scenario_count": 12,
        "twin": {"n_nodes": 20, "timesteps": 10},
    }
    manifest = generate_dataset(config, tmp_path / "dataset")
    splits = [set(manifest["split_ids"][name]) for name in ("train", "validation", "test")]
    assert not (splits[0] & splits[1] or splits[0] & splits[2] or splits[1] & splits[2])
    assert len(set().union(*splits)) == 12
    scenario = tmp_path / "dataset/scenario_000000"
    assert np.load(scenario / "states.npy").shape == (10, 20, 5)
    assert np.load(scenario / "observations.npy").shape == (10, 20, 6)
    assert np.load(scenario / "observation_mask.npy").shape == (10, 20)
    inference_payload = json.loads((scenario / "observations.json").read_text(encoding="utf-8"))
    assert "states" not in inference_payload


def test_visualization_outputs_all_required_debug_views(tmp_path):
    generate_dataset(
        {"scenario_count": 3, "dataset_seed": 2, "twin": {"n_nodes": 20, "timesteps": 10}},
        tmp_path / "dataset",
    )
    outputs = visualize_scenario(tmp_path / "dataset/scenario_000000", tmp_path / "plots")
    assert len(outputs) == 4
    assert all(path.exists() and path.stat().st_size > 0 for path in outputs)
