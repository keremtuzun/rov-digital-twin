"""Bounded, from-scratch synthetic research; never physical readiness certification."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from torch import nn

from .failure_twin import FailureScenario, _add_defect, _apply_water_conditions, _structure_geometry
from .model2.evidence_memory import EvidenceMemory
from .model2.graph_baselines import GraphBaseline
from .model2.independent_mlp import fit_train_preprocessing, transform_inputs
from .model2.simulator import TwinConfig, generate_scenario
from .model2.temporal_gru import TemporalGRU


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def visual_scene(seed, scene_index, config, shifted=False):
    """Several independently labelled views share one split group, never across splits.

    Labels describe renderer operations, NOT expert-confirmed physical defects.
    Background, pose and visibility are sampled independently of defect labels.
    """
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    size = config["image_size"]
    classes = config["classes"]
    images, labels = [], []
    structure = rng.choice(["pipe", "joint", "weld", "plate", "concrete_pier"])
    base_color = tuple(rng.randint(12, 90) for _ in range(3))
    selected_labels = rng.sample(range(len(classes)), config["images_per_scene"])
    for view in range(config["images_per_scene"]):
        label = selected_labels[view]
        severity = rng.choice(["mild", "moderate", "severe", "critical"])
        scenario = FailureScenario(
            scenario_id=f"restart_{seed}_{view}", structure_type=structure,
            material_type="steel", defect_type=classes[label] if label else "crack",
            severity=severity, spatial_pattern="localized", seed=seed + view,
            width=128, height=128, turbidity=rng.uniform(0.1, 0.75 if shifted else 0.5),
            low_light=rng.uniform(0, 0.7 if shifted else 0.4),
            blur_radius=rng.uniform(0.5, 2.5) if shifted else rng.uniform(0, 1),
            backscatter=rng.uniform(0, 0.6 if shifted else 0.3),
            contrast=rng.uniform(0.4, 1.1),
        )
        image = Image.new("RGB", (128, 128), base_color)
        _structure_geometry(ImageDraw.Draw(image), scenario)
        if label:
            _add_defect(image, Image.new("L", image.size), scenario, rng)
        image = image.rotate(rng.uniform(-60, 60) if shifted else rng.uniform(-30, 30),
                             resample=Image.Resampling.BILINEAR, fillcolor=base_color)
        image = _apply_water_conditions(image, scenario, rng)
        image = ImageEnhance.Color(image).enhance(rng.uniform(0.1, 1.7))
        if shifted:
            image = image.filter(ImageFilter.GaussianBlur(0.4))
        array = np.asarray(image.resize((size, size)), dtype=np.float32)
        # A different nuisance texture in each view avoids identical normal frames.
        array += nrng.normal(0, 6 if shifted else 3, array.shape)
        images.append(np.clip(array, 0, 255).astype(np.uint8).transpose(2, 0, 1))
        labels.append(label)
    return np.stack(images), np.asarray(labels, dtype=np.int64)


def structural_scenario(seed, config, shifted=False):
    rng = random.Random(seed)
    twin = TwinConfig(
        n_nodes=config["nodes"], timesteps=config["timesteps"],
        structure_types=(rng.choice(["chain", "branched_pipeline", "small_lattice", "mixed_structure"]),),
        observation_coverage=rng.uniform(0.08, 0.22) if shifted else rng.uniform(0.2, 0.85),
        intrinsic_degradation=rng.uniform(0.035, 0.055) if shifted else rng.uniform(0.004, 0.035),
        neighbor_coupling=rng.uniform(0.35, 0.5) if shifted else rng.uniform(0.03, 0.35),
        environment_effect_weight=rng.uniform(0.005, 0.04), environment_level=rng.random(),
        noise_std=rng.uniform(0.005, 0.04),
        severity_noise_std=rng.uniform(0.16, 0.24) if shifted else rng.uniform(0.03, 0.15),
        confidence_noise_std=rng.uniform(0.02, 0.12),
        false_positive_rate=rng.uniform(0, 0.12), false_negative_rate=rng.uniform(0.02, 0.18),
    )
    scenario = generate_scenario(f"restart_{seed}", twin, seed)
    lookup = {node.component_id: i for i, node in enumerate(scenario.graph.nodes)}
    graph = np.zeros((config["nodes"], config["nodes"]), dtype=np.float32)
    for a, b in scenario.graph.edges:
        graph[lookup[a], lookup[b]] = graph[lookup[b], lookup[a]] = 1
    return scenario.observation_tensor, scenario.observation_mask, graph, scenario.states


def build_data(output, protocol):
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for split_index, (split, count) in enumerate(protocol["splits"].items()):
        visual, labels, observations, masks, graphs, states = [], [], [], [], [], []
        seeds = []
        for index in range(count):
            seed = protocol["dataset_seed"] + split_index * 100000 + index * 10
            x, y = visual_scene(seed, index, protocol["model1"], split == "ood")
            obs, mask, graph, state = structural_scenario(seed + 1, protocol["model2"], split == "ood")
            visual.append(x)
            labels.append(y)
            observations.append(obs)
            masks.append(mask)
            graphs.append(graph)
            states.append(state)
            seeds.append(seed)
        np.savez_compressed(output / f"{split}.npz", images=np.stack(visual), labels=np.stack(labels),
                            observations=np.stack(observations), masks=np.stack(masks),
                            graphs=np.stack(graphs), states=np.stack(states))
        records.append({"split": split, "scene_seeds": seeds, "scenario_seeds": [s + 1 for s in seeds],
                        "groups": count, "sha256": digest(output / f"{split}.npz")})
        print(f"Generated {split}: {count} independent groups", flush=True)
    manifest = {"synthetic_only": True, "labels": "renderer operations and simulator latent states",
                "human_reviewed": False, "records": records,
                "model1_classes": protocol["model1"]["classes"],
                "limitations": ["2D renderer, not physically based imaging",
                                "M2 observations use a simulator, not the newly trained M1",
                                "No ecology/debris full-taxonomy training or physical strength labels"]}
    write_json(output / "manifest.json", manifest)
    return manifest


class VisualCNN(nn.Module):
    def __init__(self, width, classes):
        super().__init__()
        layers = []
        channels = 3
        for out in (width, width * 2, width * 4):
            layers += [nn.Conv2d(channels, out, 3, padding=1), nn.GroupNorm(4, out),
                       nn.SiLU(), nn.MaxPool2d(2)]
            channels = out
        self.features = nn.Sequential(*layers, nn.AdaptiveAvgPool2d((2, 2)), nn.Flatten())
        self.head = nn.Linear(width * 16, classes)

    def forward(self, x):
        return self.head(self.features(x))


def make_model(model_id, candidate, protocol):
    if model_id == "model1":
        return VisualCNN(candidate["width"], len(protocol[model_id]["classes"]))
    width = candidate["width"]
    if candidate["kind"] == "gru":
        return TemporalGRU(7, width, 1, 5, 0)
    if candidate["kind"] == "memory":
        return EvidenceMemory(width, "no_uncertainty")
    return GraphBaseline(7, 5, {"aggregation": "mean", "hidden_dimension": width,
                               "message_passing_layers": 2, "dropout": 0.1,
                               "temporal_layers": 1}, temporal=True)


def forward_model(model, model_id, x):
    if model_id == "model1":
        return model(x[0])
    features, graph, mask, confidence = x
    if isinstance(model, TemporalGRU):
        return model(features)
    if isinstance(model, EvidenceMemory):
        return model(features, graph, mask, confidence)[0]
    return model(features, graph)


def tensors(data, model_id, prep=None):
    if model_id == "model1":
        images = data["images"]
        return ([torch.from_numpy(images.reshape(-1, *images.shape[2:]).astype(np.float32) / 255)],
                torch.from_numpy(data["labels"].reshape(-1)))
    obs, mask = data["observations"], data["masks"]
    return ([torch.from_numpy(v) for v in (
        transform_inputs(obs, mask, prep), data["graphs"], mask.astype(np.float32), obs[..., 5])],
        torch.from_numpy(data["states"]))


def predict(model, model_id, inputs):
    model.eval()
    outputs = []
    with torch.no_grad():
        for start in range(0, len(inputs[0]), 64):
            out = forward_model(model, model_id, [x[start:start + 64] for x in inputs])
            if model_id == "model1":
                out = out.softmax(-1)
            if not torch.isfinite(out).all():
                raise ValueError("nonfinite prediction")
            outputs.append(out.cpu().numpy())
    return np.concatenate(outputs)


def classification_metrics(prob, labels):
    predicted = prob.argmax(-1)
    cm = np.zeros((prob.shape[-1], prob.shape[-1]), dtype=np.int64)
    np.add.at(cm, (labels, predicted), 1)
    tp = np.diag(cm)
    recall = tp / np.maximum(cm.sum(1), 1)
    f1 = 2 * tp / np.maximum(cm.sum(0) + cm.sum(1), 1)
    return {"macro_f1": float(f1.mean()), "accuracy": float(np.mean(predicted == labels)),
            "minimum_class_recall": float(recall.min()), "recall": recall.tolist(),
            "confusion_matrix": cm.tolist()}


def score(model_id, predicted, target):
    if model_id == "model1":
        return classification_metrics(predicted, target.numpy())["macro_f1"]
    return -float(np.abs(predicted.astype(np.float64) - target.numpy()).mean())


def train_run(model_id, candidate, seed, protocol, train, val, output, prep):
    output.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    model = make_model(model_id, candidate, protocol)
    tx, ty = tensors(train, model_id, prep)
    vx, vy = tensors(val, model_id, prep)
    optimizer = torch.optim.AdamW(model.parameters(), lr=candidate["lr"], weight_decay=1e-4)
    config = protocol[model_id]
    best, stale, history, best_state = -math.inf, 0, [], None
    best_epoch = 0
    for epoch in range(1, config["maximum_epochs"] + 1):
        model.train()
        losses = []
        for ids in torch.randperm(len(ty)).split(64 if model_id == "model1" else 32):
            batch = [x[ids] for x in tx]
            if model_id == "model1" and candidate["augmentation"]:
                image = batch[0]
                if torch.rand(()) < 0.5:
                    image = image.flip(-1)
                image = (image * (0.8 + 0.4 * torch.rand(len(ids), 1, 1, 1))
                         + 0.02 * torch.randn_like(image)).clamp(0, 1)
                batch = [image]
            prediction = forward_model(model, model_id, batch)
            if model_id == "model1":
                loss = nn.functional.cross_entropy(prediction, ty[ids])
            elif candidate["loss"] == "huber":
                loss = nn.functional.smooth_l1_loss(prediction, ty[ids], beta=0.1)
            else:
                loss = nn.functional.mse_loss(prediction, ty[ids])
            if not torch.isfinite(loss):
                raise ValueError("nonfinite training loss")
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1, error_if_nonfinite=True)
            optimizer.step()
            losses.append(float(loss.detach()))
        validation = score(model_id, predict(model, model_id, vx), vy)
        improvement = validation - best
        if validation > best:
            best, best_epoch = validation, epoch
            best_state = copy.deepcopy(model.state_dict())
        stale = 0 if improvement >= config["minimum_improvement"] else stale + 1
        history.append({"epoch": epoch, "loss": float(np.mean(losses)), "validation_score": validation})
        write_json(output / "history.json", history)
        if epoch % 5 == 0:
            print(f"{model_id}/{candidate['name']}/{seed} epoch={epoch} val={validation:.6f}", flush=True)
        if stale >= config["patience"]:
            break
    torch.save({"state_dict": best_state, "candidate": candidate, "model_id": model_id,
                "preprocessing": prep, "seed": seed}, output / "checkpoint.pt")
    result = {"model_id": model_id, "candidate": candidate["name"], "seed": seed,
              "validation_score": best, "epoch": best_epoch, "epochs_run": len(history),
              "stop_reason": "validation_patience" if stale >= config["patience"] else "epoch_budget",
              "sha256": digest(output / "checkpoint.pt"), "locked_at": now()}
    write_json(output / "selection.json", result)
    print(f"Completed {model_id}/{candidate['name']}/{seed}: {best:.6f}", flush=True)
    return result


def conformal_quantile(scores, alpha=0.1):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("calibration scores must be nonempty and finite")
    rank = math.ceil((len(scores) + 1) * (1 - alpha))
    if rank > len(scores):
        raise ValueError("insufficient calibration groups")
    return float(np.sort(scores)[rank - 1])


def search_summary(runs, candidates, threshold):
    scores = {c["name"]: float(np.mean([r["validation_score"] for r in runs
                                      if r["candidate"] == c["name"]])) for c in candidates}
    rounds, previous, stale = [], -math.inf, 0
    for start in range(0, len(candidates), 2):
        current = max(scores[c["name"]] for c in candidates[start:start + 2])
        improved = current - previous >= threshold
        stale = 0 if improved else stale + 1
        previous = max(previous, current)
        rounds.append({"round": start // 2 + 1, "best_score_so_far": previous,
                       "meaningful_improvement": improved})
    return {"selected": max(scores, key=scores.get), "validation_scores": scores,
            "rounds": rounds, "status": "bounded_search_plateau" if stale >= 2 else "budget_exhausted",
            "global_optimum_proven": False, "physical_data_is_only_remaining_improvement": False}


def run(root, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports" / protocol["experiment_id"]
    if output.exists():
        raise FileExistsError("Restart experiment exists; do not overwrite or repeat held-out evaluation")
    output.mkdir(parents=True)
    write_json(output / "protocol.json", protocol)
    write_json(output / "environment.json", {"torch": str(torch.__version__), "numpy": np.__version__,
               "device": "cpu", "threads": torch.get_num_threads(), "started_at": now(),
               "source_sha256": digest(Path(__file__)), "protocol_sha256": digest(protocol_path)})
    data_dir = root / "data" / protocol["experiment_id"]
    build_data(data_dir, protocol)
    train = dict(np.load(data_dir / "train.npz", allow_pickle=False))
    val = dict(np.load(data_dir / "validation.npz", allow_pickle=False))
    prep = fit_train_preprocessing(train["observations"], train["masks"])
    all_runs, selected = {}, {}
    for model_id in ("model1", "model2"):
        runs = []
        for candidate in protocol[model_id]["candidates"]:
            for seed in protocol["training_seeds"]:
                runs.append(train_run(model_id, candidate, seed, protocol, train, val,
                                      output / model_id / candidate["name"] / str(seed), prep))
        all_runs[model_id] = runs
        selected[model_id] = search_summary(runs, protocol[model_id]["candidates"],
                                             protocol[model_id]["minimum_improvement"])
    write_json(output / "matrix_locked.json", {"locked_at": now(), "runs": all_runs, "selection": selected})
    del train, val
    summary = {"selection": selected, "synthetic_only": True, "deployment_authorized": False,
               "full_model1_taxonomy_trained": False, "real_model1_to_model2_integration_validated": False,
               "models": {}}
    for model_id in ("model1", "model2"):
        candidate = next(c for c in protocol[model_id]["candidates"] if c["name"] == selected[model_id]["selected"])
        models = []
        for seed in protocol["training_seeds"]:
            checkpoint = torch.load(output / model_id / candidate["name"] / str(seed) / "checkpoint.pt",
                                    weights_only=True)
            model = make_model(model_id, candidate, protocol)
            model.load_state_dict(checkpoint["state_dict"])
            models.append(model)
        results = {}
        for split in ("calibration", "test", "ood"):
            data = dict(np.load(data_dir / f"{split}.npz", allow_pickle=False))
            inputs, targets = tensors(data, model_id, prep)
            prediction = np.mean([predict(m, model_id, inputs) for m in models], axis=0)
            np.save(output / f"{model_id}_{split}_predictions.npy", prediction)
            target = targets.numpy()
            if model_id == "model1":
                scores = (1 - prediction[np.arange(len(target)), target]).reshape(len(data["labels"]), -1).max(1)
                if split == "calibration":
                    quantile = conformal_quantile(scores)
                sets = (1 - prediction) <= quantile
                results[split] = classification_metrics(prediction, target)
                results[split].update(scene_set_coverage=float(np.mean(scores <= quantile)),
                                      mean_set_size=float(sets.sum(1).mean()),
                                      singleton_fraction=float(np.mean(sets.sum(1) == 1)))
            else:
                errors = np.abs(prediction.astype(np.float64) - target)
                scores = errors.reshape(len(target), -1).max(1)
                if split == "calibration":
                    quantile = conformal_quantile(scores)
                lower, upper = np.maximum(0, prediction - quantile), np.minimum(1, prediction + quantile)
                results[split] = {"mae": float(errors.mean()), "rmse": float(np.sqrt((errors ** 2).mean())),
                                  "unobserved_mae": float(errors[data["masks"] == 0].mean()),
                                  "simultaneous_trajectory_coverage": float(np.mean(scores <= quantile)),
                                  "mean_interval_width": float((upper - lower).mean())}
            del data, inputs, targets
        results["calibration_quantile"] = quantile
        results["ood_coverage_guaranteed"] = False
        summary["models"][model_id] = results
    write_json(output / "summary.json", summary)
    write_json(output / "completed.json", {"completed_at": now(), "heldout_evaluations": 1,
               "files": {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob("*"))
                         if p.is_file()}})
    return summary
