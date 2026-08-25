"""Debug-only visualizations for Failure Twin v0 hidden truth and observation masks."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def visualize_scenario(scenario_dir: str | Path, output_dir: str | Path) -> list[Path]:
    source, output = Path(scenario_dir), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    states = np.load(source / "states.npy")
    observations = np.load(source / "observations.npy")
    mask = np.load(source / "observation_mask.npy")
    structure = json.loads((source / "structure.json").read_text(encoding="utf-8"))
    outputs: list[Path] = []

    fig, axis = plt.subplots(figsize=(8, 4))
    selected = sorted({0, states.shape[1] // 2, states.shape[1] - 1})
    for node_index in selected:
        axis.plot(states[:, node_index, 4], label=f"component_{node_index:03d} true")
        observed = np.where(
            mask[:, node_index] == 1, observations[:, node_index, 4], np.nan
        )
        axis.scatter(range(states.shape[0]), observed, marker="x", label=f"node {node_index} observed")
    axis.set(title="DEBUG GROUND TRUTH: condition and observation availability", xlabel="timestep",
             ylabel="condition")
    axis.legend(fontsize=7)
    path = output / "debug_true_vs_observed.png"
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    outputs.append(path)

    graph = nx.Graph()
    graph.add_nodes_from(node["component_id"] for node in structure["nodes"])
    graph.add_edges_from(structure["edges"])
    fig, axis = plt.subplots(figsize=(8, 5))
    positions = nx.spring_layout(graph, seed=int(structure["seed"]))
    nx.draw_networkx(
        graph, positions, ax=axis, node_size=240, font_size=5,
        node_color=states[-1, :, 4], cmap="inferno", vmin=0, vmax=1,
    )
    axis.set_title("DEBUG GROUND TRUTH: final hidden condition")
    axis.axis("off")
    path = output / "debug_graph_hidden_condition.png"
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    outputs.append(path)

    fig, axis = plt.subplots(figsize=(8, 4))
    axis.imshow(mask.T, aspect="auto", interpolation="nearest", cmap="Greys")
    axis.set(title="Observation mask (1=observed, 0=missing)", xlabel="timestep",
             ylabel="component index")
    path = output / "observation_mask.png"
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    outputs.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    axes[0].hist(states[0, :, 4], bins=10, range=(0, 1))
    axes[0].set_title("DEBUG GROUND TRUTH: initial condition")
    axes[1].hist(states[-1, :, 4], bins=10, range=(0, 1))
    axes[1].set_title("DEBUG GROUND TRUTH: final condition")
    for axis in axes:
        axis.set(xlabel="condition", ylabel="node count")
    path = output / "debug_condition_histograms.png"
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    outputs.append(path)
    return outputs
