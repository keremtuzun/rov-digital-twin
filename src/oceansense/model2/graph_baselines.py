"""Conventional graph baselines: topology-only mean messages, optionally causal memory.

Inference accepts observations+mask and adjacency only, never simulator state or metadata.
"""

from __future__ import annotations

import json

import numpy as np
import torch
from torch import nn

from .independent_mlp import S1Data


def load_adjacency(data: S1Data) -> np.ndarray:
    """Align graphs by scenario ID and nodes by explicit tensor_index, not JSON order."""
    payload = json.loads((data.release_dir / "structure_graph.json").read_text())
    graphs = payload["scenario_graphs"]
    lookup = {graph["scenario_id"]: graph for graph in graphs}
    ids = data.metadata["scenario_ids"]
    if len(lookup) != len(graphs) or set(lookup) != set(ids):
        raise ValueError("graph scenario IDs must match the release exactly")
    nodes = data.observations.shape[2]
    result = np.zeros((len(ids), nodes, nodes), dtype=np.float32)
    for index, scenario_id in enumerate(ids):
        graph = lookup[scenario_id]
        mapping = {node["component_id"]: node["tensor_index"] for node in graph["nodes"]}
        if len(mapping) != nodes or set(mapping.values()) != set(range(nodes)):
            raise ValueError("graph nodes must have unique contiguous tensor indices")
        for edge in graph["edges"]:
            if edge["source"] not in mapping or edge["target"] not in mapping:
                raise ValueError("graph edge refers to an unknown component")
            left, right = mapping[edge["source"]], mapping[edge["target"]]
            if left == right:
                raise ValueError("self edges are not part of the structural-neighbor contract")
            result[index, left, right] = result[index, right, left] = 1.0
    return result


class GraphBaseline(nn.Module):
    """Two mean-message layers; Temporal GNN then applies a node-shared causal GRU.

    Static GNN has no persistent memory. Temporal GNN resets memory each call/scenario.
    Node type, criticality, scenario IDs and simulator parameters are NOT features.
    """

    def __init__(
        self, input_dim: int, output_dim: int, architecture: dict, temporal: bool = False
    ) -> None:
        super().__init__()
        if architecture["aggregation"] != "mean":
            raise ValueError("only mean aggregation is supported")
        if architecture.get("bidirectional") or architecture.get("uses_future_context"):
            raise ValueError("graph baselines must remain causal")
        self.temporal = temporal
        width = architecture["hidden_dimension"]
        self.encoder = nn.Linear(input_dim, width)
        self.messages = nn.ModuleList(
            [nn.Linear(width * 2, width) for _ in range(architecture["message_passing_layers"])]
        )
        self.dropout = nn.Dropout(architecture["dropout"])
        if temporal:
            self.gru = nn.GRU(
                width,
                width,
                num_layers=architecture["temporal_layers"],
                batch_first=True,
                bidirectional=False,
            )
        self.head = nn.Sequential(nn.Linear(width, output_dim), nn.Sigmoid())

    def forward(self, inputs: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4 or adjacency.shape != (
            inputs.shape[0],
            inputs.shape[2],
            inputs.shape[2],
        ):
            raise ValueError(
                "expected inputs [batch,time,node,feature], adjacency [batch,node,node]"
            )
        if not torch.isfinite(inputs).all() or not torch.isfinite(adjacency).all():
            raise ValueError("inputs and adjacency must be finite")
        if torch.any(adjacency < 0):
            raise ValueError("adjacency weights cannot be negative")
        mean_neighbors = adjacency / adjacency.sum(-1, keepdim=True).clamp_min(1)
        hidden = torch.relu(self.encoder(inputs))
        for layer in self.messages:
            neighbors = torch.matmul(mean_neighbors[:, None], hidden)
            hidden = self.dropout(torch.relu(layer(torch.cat((hidden, neighbors), dim=-1))))
        if self.temporal:
            batch, timesteps, nodes, width = hidden.shape
            sequences = hidden.permute(0, 2, 1, 3).reshape(batch * nodes, timesteps, width)
            sequences, _ = self.gru(sequences)
            hidden = sequences.reshape(batch, nodes, timesteps, width).permute(0, 2, 1, 3)
        return self.head(hidden)


def masked_mse(
    predictions: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Observed-only loss preserves S1 protocol; reject empty supervision instead of NaN."""
    selected = mask.bool()
    if not selected.any():
        raise ValueError("batch has no observed supervision")
    loss = (predictions[selected] - targets[selected]).square().mean()
    if not torch.isfinite(loss):
        raise ValueError("non-finite training loss")
    return loss
