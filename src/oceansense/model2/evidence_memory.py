"""Experimental evidence-gated structural memory; no physical or novelty claim."""

from __future__ import annotations

import torch
from torch import nn


class EvidenceMemory(nn.Module):
    def __init__(self, width=32, variant="full"):
        super().__init__()
        if variant not in {"full", "no_memory", "no_graph", "no_gate", "no_uncertainty"}:
            raise ValueError("unknown evidence-memory variant")
        self.variant, self.width = variant, width
        self.encoder = nn.Sequential(nn.Linear(7, width), nn.ReLU())
        self.prior = nn.Sequential(nn.Linear(2 * width, width), nn.Tanh())
        self.cell = nn.GRUCell(2 * width, width)
        self.gate = nn.Linear(3 * width, width)
        self.mean = nn.Sequential(nn.Linear(width, 5), nn.Sigmoid())
        self.variance = nn.Linear(width, 5) if variant != "no_uncertainty" else None

    def forward(self, features, adjacency, mask, confidence):
        if features.ndim != 4 or features.shape[-1] != 7:
            raise ValueError("features must be [batch,time,node,7]")
        batch, times, nodes, _ = features.shape
        if adjacency.shape != (batch, nodes, nodes) or mask.shape != (batch, times, nodes):
            raise ValueError("graph/mask shape mismatch")
        if confidence.shape != mask.shape:
            raise ValueError("confidence shape mismatch")
        if not all(torch.isfinite(x).all() for x in (features, adjacency, mask, confidence)):
            raise ValueError("non-finite inference input")
        if torch.any((mask != 0) & (mask != 1)) or torch.any(adjacency < 0):
            raise ValueError("invalid mask or graph")
        if torch.any((confidence < 0) | (confidence > 1)):
            raise ValueError("confidence must be in [0,1]")
        graph = adjacency / adjacency.sum(-1, keepdim=True).clamp_min(1)
        hidden = features.new_zeros(batch, nodes, self.width)
        means, variances = [], []
        for time in range(times):
            if self.variant == "no_memory":
                hidden = torch.zeros_like(hidden)
            observed = mask[:, time, :, None]
            # Missing feature values cannot influence the encoder, even if caller forgets imputation.
            current = features[:, time] * observed
            encoded = self.encoder(current)
            neighbors = torch.bmm(graph, hidden)
            if self.variant == "no_graph":
                neighbors = torch.zeros_like(neighbors)
            prior = self.prior(torch.cat((hidden, neighbors), -1))
            candidate = self.cell(
                torch.cat((encoded, neighbors), -1).reshape(-1, 2 * self.width),
                hidden.reshape(-1, self.width),
            ).reshape(batch, nodes, self.width)
            if self.variant == "no_gate":
                gate = observed
            else:
                gate = (
                    torch.sigmoid(self.gate(torch.cat((encoded, hidden, neighbors), -1)))
                    * observed
                    * confidence[:, time, :, None]
                )
            hidden = prior + gate * (candidate - prior)
            means.append(self.mean(hidden))
            if self.variance is not None:
                variances.append(torch.nn.functional.softplus(self.variance(hidden)).clamp(1e-4, 1))
        return torch.stack(means, 1), torch.stack(variances, 1) if variances else None
