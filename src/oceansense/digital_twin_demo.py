"""Artifact integration between navigation replay and the separate 2D visual fixture.

This command does not import, execute, train, or validate Model 2 or Failure Twin v0.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .experiment import PredictionRecord, RunManifest, write_jsonl, write_run_manifest
from .failure_twin import FailureScenario, generate_pair
from .mission_decision import MissionDecisionInput, decide_mission
from .navigation_contracts import write_navigation_bundle
from .navigation_twin import NavigationMissionConfig, simulate_navigation


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_report(payload: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Digital twin demo report: {payload['run_id']}",
        "",
        "## Traceability",
        "",
        "```json",
        json.dumps(payload["traceability"], indent=2, sort_keys=True),
        "```",
        "",
        "## Navigation metrics",
        "",
        "```json",
        json.dumps(payload["navigation_metrics"], indent=2, sort_keys=True),
        "```",
        "",
        "## Synthetic ground truth",
        "",
        "```json",
        json.dumps(payload["ground_truth"], indent=2, sort_keys=True),
        "```",
        "",
        "## Placeholder baseline and decision",
        "",
        "```json",
        json.dumps({"prediction": payload["prediction"], "decision": payload["decision"]},
                   indent=2, sort_keys=True),
        "```",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in payload["limitations"]],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_demo(
    *,
    navigation_config_path: str | Path,
    failure_config_path: str | Path,
    output_dir: str | Path,
    run_id: str,
    git_commit: str,
    branch: str,
    operator_or_agent: str,
) -> dict[str, Any]:
    """Run a navigation/visual-fixture demo with linked IDs and placeholder evidence."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    failure_payload = _load(failure_config_path)
    failure_payload["intended_use"] = "demo"
    scenario = FailureScenario(**failure_payload)
    failure_metadata = generate_pair(scenario, output / "failure_twin")

    navigation_payload = _load(navigation_config_path)
    navigation_payload.update({
        "run_id": run_id,
        "scenario_id": scenario.scenario_id,
        "frame_reference": failure_metadata["output_image_path"],
    })
    navigation_config = NavigationMissionConfig.from_mapping(navigation_payload)
    navigation = simulate_navigation(navigation_config)
    if not navigation.frames:
        raise RuntimeError("navigation twin did not reach the configured capture distance")
    frame = navigation.frames[0]
    target = navigation.targets[0]
    linked_ids = {
        "mission_id": (navigation_config.mission_id, frame.mission_id, target.mission_id),
        "target_id": (navigation_config.target_id, frame.target_id, target.target_id),
        "scenario_id": (scenario.scenario_id, frame.scenario_id, target.scenario_id),
        "run_id": (run_id, frame.run_id, target.run_id),
    }
    mismatches = {
        name: values for name, values in linked_ids.items()
        if len(set(values)) != 1 or any(value is None or not str(value).strip() for value in values)
    }
    if mismatches:
        raise RuntimeError(f"navigation/visual-fixture shared ID mismatch: {mismatches}")
    bundle_paths = write_navigation_bundle(
        output / "navigation_twin",
        states=navigation.states,
        frames=navigation.frames,
        targets=navigation.targets,
        events=navigation.events,
    )

    prediction = PredictionRecord(
        run_id=run_id,
        model_name="placeholder_no_frozen_model1",
        model_version="placeholder-v1",
        frame_id=frame.frame_id,
        target_id=target.target_id,
        prediction_type="class",
        class_label="unknown",
        confidence=0.0,
        uncertainty={"unknown": True},
        evidence_refs=[frame.frame_id],
        metadata={
            "scenario_id": scenario.scenario_id,
            "synthetic_or_real": "synthetic",
            "not_a_metric": True,
            "ground_truth_defect_type": scenario.defect_type,
        },
    )
    prediction_path = write_jsonl([prediction], output / "predictions.jsonl")
    decision_request = MissionDecisionInput(
        mission_id=navigation_config.mission_id,
        frame_id=frame.frame_id,
        robot_pose=frame.robot_pose_at_capture,
        inspection_target=target,
        model1_outputs=[asdict(prediction)],
        model2_outputs=[],
        uncertainty={"unknown": True, "entropy": 1.0},
        environment={
            "visibility": navigation_config.visibility_condition,
            "turbidity": navigation_config.turbidity_value,
            "lighting": navigation_config.lighting_condition,
        },
    )
    decision = decide_mission(decision_request)
    decision_path = output / "decision.json"
    decision_path.write_text(json.dumps(asdict(decision), indent=2, sort_keys=True), encoding="utf-8")

    traceability = {
        "run_id": run_id,
        "mission_id": navigation_config.mission_id,
        "frame_id": frame.frame_id,
        "target_id": target.target_id,
        "scenario_id": scenario.scenario_id,
        "robot_pose": asdict(frame.robot_pose_at_capture),
        "frame_reference": frame.frame_reference,
        "ground_truth_mask": failure_metadata["mask_path"],
        "synthetic_or_real": "synthetic",
    }
    if any(not str(traceability[name]).strip() for name in
           ("run_id", "mission_id", "frame_id", "target_id", "scenario_id")):
        raise RuntimeError("navigation/visual-fixture traceability contains an empty shared ID")
    trace_path = output / "integration_trace.json"
    trace_path.write_text(json.dumps(traceability, indent=2, sort_keys=True), encoding="utf-8")
    limitations = [
        "The inspection evidence and ground truth are synthetic 2D generator outputs.",
        "The navigation path is a deterministic kinematic replay, not Unity hydrodynamics.",
        "No frozen Model 1 exists; the placeholder deliberately returns unknown with zero confidence.",
        "The decision is a high-level software recommendation and has no actuator authority.",
        "This demo proves interface traceability, not real-world accuracy or physical calibration.",
    ]
    report_payload = {
        "run_id": run_id,
        "traceability": traceability,
        "navigation_metrics": navigation.metrics,
        "ground_truth": failure_metadata["ground_truth"],
        "prediction": asdict(prediction),
        "decision": asdict(decision),
        "limitations": limitations,
    }
    report_json = output / "digital_twin_demo_report.json"
    report_markdown = output / "digital_twin_demo_report.md"

    failure_outputs = list(failure_metadata["artifacts"].values()) + [
        str(output / "failure_twin" / f"{scenario.scenario_id}.json")
    ]
    outputs = failure_outputs + [str(path) for path in bundle_paths.values()] + [
        str(prediction_path), str(decision_path), str(trace_path),
        str(report_json), str(report_markdown), str(output / "run_manifest.json"),
    ]
    manifest = RunManifest(
        run_id=run_id,
        date=datetime.now(timezone.utc).isoformat(),
        git_commit=git_commit,
        branch=branch,
        operator_or_agent=operator_or_agent,
        track="integration",
        config_path=str(navigation_config_path),
        dataset_manifest=str(output / "failure_twin" / f"{scenario.scenario_id}.json"),
        checkpoint_or_prototype_version="placeholder_no_frozen_model1",
        inputs=[str(navigation_config_path), str(failure_config_path)],
        outputs=outputs,
        metrics={"navigation": navigation.metrics, "traceability_complete": True},
        synthetic_or_real_or_mixed="synthetic",
        limitations=limitations,
        next_actions=[
            "Replace the placeholder only after Model 1 has an approved freeze package.",
            "Replay an equivalent mission through Unity and compare navigation metrics.",
        ],
    )
    manifest_path = write_run_manifest(manifest, output / "run_manifest.json")
    report_payload["run_manifest"] = str(manifest_path)
    report_json.write_text(
        json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    _write_report(report_payload, report_markdown)
    return report_payload
