"""Fresh, bounded larger-graph search after the first search remained open."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .local_restart import conformal_quantile, digest, now, structural_scenario, write_json
from .model2.graph_baselines import GraphBaseline
from .model2.independent_mlp import fit_train_preprocessing, transform_inputs


def make_model(candidate):
    return GraphBaseline(7, 5, {"aggregation": "mean", "hidden_dimension": candidate["width"],
        "message_passing_layers": candidate["layers"], "dropout": candidate["dropout"],
        "temporal_layers": 1}, temporal=True)


def load_split(path):
    return dict(np.load(path, allow_pickle=False))


def build_data(path, protocol):
    path.mkdir(parents=True, exist_ok=False)
    records = []
    for split_index, (split, count) in enumerate(protocol["splits"].items()):
        values = [structural_scenario(protocol["dataset_seed"] + split_index * 100000 + i * 10,
                                      protocol, split == "ood") for i in range(count)]
        np.savez_compressed(path / f"{split}.npz", observations=np.stack([v[0] for v in values]),
                            masks=np.stack([v[1] for v in values]), graphs=np.stack([v[2] for v in values]),
                            states=np.stack([v[3] for v in values]))
        records.append({"split": split, "groups": count, "sha256": digest(path / f"{split}.npz")})
        print(f"Extended Model 2 data {split}: {count}", flush=True)
    write_json(path / "manifest.json", {"synthetic_only": True, "records": records,
               "real_world_validation": False, "physical_data_is_only_remaining_improvement": False})


def inputs(data, prep):
    return [torch.from_numpy(x) for x in (transform_inputs(data["observations"], data["masks"], prep),
            data["graphs"], data["states"])]


def predict(model, features, graphs):
    model.eval()
    output = []
    with torch.no_grad():
        for start in range(0, len(features), 32):
            value = model(features[start:start + 32], graphs[start:start + 32])
            if not torch.isfinite(value).all():
                raise ValueError("nonfinite extended prediction")
            output.append(value.numpy())
    return np.concatenate(output)


def run(root):
    protocol_path = root / "configs/model2_extended_v1.json"
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports" / protocol["experiment_id"]
    data_path = root / "data" / protocol["experiment_id"]
    if output.exists() or data_path.exists():
        raise FileExistsError("extended experiment already exists; refusing held-out rerun")
    output.mkdir(parents=True)
    write_json(output / "protocol.json", protocol)
    write_json(output / "environment.json", {"source_sha256": digest(Path(__file__)),
               "protocol_sha256": digest(protocol_path), "torch": str(torch.__version__), "started_at": now()})
    build_data(data_path, protocol)
    train, val = load_split(data_path / "train.npz"), load_split(data_path / "validation.npz")
    prep = fit_train_preprocessing(train["observations"], train["masks"])
    tx, tg, ty = inputs(train, prep)
    vx, vg, vy = inputs(val, prep)
    runs = []
    for candidate in protocol["candidates"]:
        for seed in protocol["training_seeds"]:
            torch.manual_seed(seed)
            model = make_model(candidate)
            optimizer = torch.optim.AdamW(model.parameters(), lr=candidate["lr"], weight_decay=0.0001)
            best, stale, state, history = math.inf, 0, None, []
            directory = output / candidate["name"] / str(seed)
            directory.mkdir(parents=True)
            for epoch in range(1, protocol["maximum_epochs"] + 1):
                model.train()
                for ids in torch.randperm(len(ty)).split(32):
                    prediction = model(tx[ids], tg[ids])
                    loss = nn.functional.smooth_l1_loss(prediction, ty[ids], beta=0.1)
                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1, error_if_nonfinite=True)
                    optimizer.step()
                prediction = predict(model, vx, vg)
                value = float(np.abs(prediction.astype(np.float64) - vy.numpy()).mean())
                gain = best - value
                if value < best:
                    best, best_epoch, state = value, epoch, copy.deepcopy(model.state_dict())
                stale = 0 if gain >= protocol["minimum_improvement"] else stale + 1
                history.append({"epoch": epoch, "validation_mae": value})
                if epoch % 5 == 0:
                    print(f"Extended {candidate['name']}/{seed} epoch={epoch} mae={value:.5f}", flush=True)
                if stale >= protocol["patience"]:
                    break
            torch.save({"state_dict": state, "candidate": candidate, "preprocessing": prep},
                       directory / "checkpoint.pt")
            write_json(directory / "history.json", history)
            record = {"candidate": candidate["name"], "seed": seed, "validation_mae": best,
                      "epoch": best_epoch, "sha256": digest(directory / "checkpoint.pt")}
            write_json(directory / "selection.json", record)
            runs.append(record)
    means = {c["name"]: float(np.mean([r["validation_mae"] for r in runs if r["candidate"] == c["name"]]))
             for c in protocol["candidates"]}
    rounds, best, stale = [], math.inf, 0
    for start in range(0, len(protocol["candidates"]), 2):
        value = min(means[c["name"]] for c in protocol["candidates"][start:start + 2])
        improved = best - value >= protocol["minimum_improvement"]
        stale = 0 if improved else stale + 1
        best = min(best, value)
        rounds.append({"round": start // 2 + 1, "best_mae_so_far": best, "meaningful_improvement": improved})
    selected = min(means, key=means.get)
    selection = {"selected": selected, "validation_mae": means, "rounds": rounds,
                 "status": "bounded_architecture_plateau" if stale >= 2 else "budget_exhausted",
                 "global_optimum_proven": False, "physical_data_is_only_remaining_improvement": False}
    write_json(output / "matrix_locked.json", {"locked_at": now(), "runs": runs, "selection": selection})
    candidate = next(c for c in protocol["candidates"] if c["name"] == selected)
    models = []
    for seed in protocol["training_seeds"]:
        model = make_model(candidate)
        model.load_state_dict(torch.load(output / selected / str(seed) / "checkpoint.pt",
                                         weights_only=True)["state_dict"])
        models.append(model)
    results = {}
    for split in ("calibration", "test", "ood"):
        data = load_split(data_path / f"{split}.npz")
        x = torch.from_numpy(transform_inputs(data["observations"], data["masks"], prep))
        graph = torch.from_numpy(data["graphs"])
        prediction = np.mean([predict(model, x, graph) for model in models], axis=0)
        np.save(output / f"{split}_predictions.npy", prediction)
        error = np.abs(prediction.astype(np.float64) - data["states"])
        scores = error.reshape(len(error), -1).max(1)
        if split == "calibration":
            quantile = conformal_quantile(scores)
        lower, upper = np.maximum(0, prediction - quantile), np.minimum(1, prediction + quantile)
        results[split] = {"mae": float(error.mean()), "rmse": float(np.sqrt((error ** 2).mean())),
            "unobserved_mae": float(error[data["masks"] == 0].mean()),
            "simultaneous_trajectory_coverage": float(np.mean(scores <= quantile)),
            "mean_interval_width": float((upper - lower).mean())}
    summary = {"selection": selection, "calibration_quantile": quantile, **results,
               "synthetic_only": True, "deployment_authorized": False,
               "physical_data_is_only_remaining_improvement": False, "ood_coverage_guaranteed": False}
    write_json(output / "summary.json", summary)
    write_json(output / "completed.json", {"completed_at": now(), "heldout_evaluations": 1,
               "files": {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob("*")) if p.is_file()}})
    return summary
