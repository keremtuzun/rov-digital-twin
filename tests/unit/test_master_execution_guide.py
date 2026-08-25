import hashlib
import json

import pytest

from oceansense.digital_twin_demo import run_demo
from oceansense.experiment import PredictionRecord, RunManifest, read_run_manifest, write_run_manifest
from oceansense.failure_twin import FailureScenario, generate_batch, generate_pair
from oceansense.mission_decision import MissionDecisionInput, decide_mission
from oceansense.model2_reasoning import (
    EvidenceObservation,
    StructuralRelation,
    StructuralTemporalReasoner,
    run_ablation,
)
from oceansense.navigation_contracts import (
    InspectionTarget,
    MissionEvent,
    RobotPose,
    SensorFrame,
    read_mission_events,
    write_mission_events,
    write_navigation_bundle,
)
from oceansense.navigation_twin import NavigationMissionConfig, simulate_navigation


def _observation(frame: int, target: str = "weld-1", score: float = 0.8):
    return EvidenceObservation(
        frame_id=f"frame-{frame}", target_id=target, timestamp=float(frame),
        component_type="weld" if target == "weld-1" else "pipe",
        condition_label="possible_structural_concern", concern_score=score,
        uncertainty=0.1, viewpoint_angle_deg=float(frame * 12), distance_m=1.0,
        evidence_ref=f"frame-{frame}",
    )


def test_failure_twin_is_reproducible_and_explicitly_synthetic(tmp_path):
    pytest.importorskip("PIL")
    scenario = FailureScenario(
        "FT-test", "pipe", "coated_steel", "crack", "moderate", "linear", 42,
    )
    first = generate_pair(scenario, tmp_path / "first")
    second = generate_pair(scenario, tmp_path / "second")
    first_bytes = (tmp_path / "first/FT-test_degraded.png").read_bytes()
    second_bytes = (tmp_path / "second/FT-test_degraded.png").read_bytes()
    assert hashlib.sha256(first_bytes).digest() == hashlib.sha256(second_bytes).digest()
    assert first["synthetic_or_real"] == "synthetic"
    assert "not physical" in first["claim_boundary"]
    assert first["scenario"] == second["scenario"]
    assert first["severity_score"] == 0.5
    assert first["box_coordinates"]


def test_failure_twin_batch_writes_disjoint_split_manifests(tmp_path):
    pytest.importorskip("PIL")
    output = tmp_path / "failure"
    records = generate_batch({"count": 24, "seed": 12, "width": 128, "height": 128}, output)
    split_sets = {
        split: {record["scenario_id"] for record in records if record["split"] == split}
        for split in ("train", "validation", "test")
    }
    assert len(records) == len(set().union(*split_sets.values()))
    assert not (split_sets["train"] & split_sets["validation"])
    assert not (split_sets["train"] & split_sets["test"])
    assert not (split_sets["validation"] & split_sets["test"])
    assert all((output / f"{split}_manifest.jsonl").exists() for split in split_sets)


def test_model2_uses_temporal_and_structural_terms_and_exports_ablations():
    observations = [_observation(index) for index in range(4)]
    observations.append(_observation(5, "pipe-1", 0.75))
    relations = [StructuralRelation("weld-1", "pipe-1", "weld_connects")]
    result = StructuralTemporalReasoner().reason("weld-1", observations, relations)
    assert result.unknown is False
    assert result.persistence == 1.0
    assert result.relationship_support > 0
    ablations = run_ablation("weld-1", observations, relations)
    assert set(ablations) == {
        "full", "without_temporal", "without_structure", "model1_score_only",
    }
    assert ablations["full"]["risk_score"] > ablations["model1_score_only"]["risk_score"]


def test_model2_requests_reinspection_with_insufficient_history():
    result = StructuralTemporalReasoner().reason("weld-1", [_observation(0)])
    assert result.unknown
    assert result.recommended_decision == "request_reinspection"


def test_navigation_contract_rejects_cross_mission_frame():
    pose = RobotPose(0, 0, -2, 0, 0, 0)
    frame = SensorFrame("f1", "mission-b", 1.0, "frame.png", None, {}, 0.2, pose)
    with pytest.raises(ValueError, match="mission_id"):
        MissionEvent("e1", "mission-a", 1.0, "inspection_started", sensor_frame=frame)


def test_navigation_event_log_round_trips_for_ui_independent_replay(tmp_path):
    pose = RobotPose(0, 0, -2, 0, 0, 5)
    frame = SensorFrame("f1", "mission-a", 1.0, "frame.png", None,
                        {"visibility": "moderate"}, 0.2, pose)
    event = MissionEvent("e1", "mission-a", 1.0, "inspection_started",
                         related_frame_id="f1", sensor_frame=frame)
    path = write_mission_events([event], tmp_path / "events.jsonl")
    assert read_mission_events(path) == [event]


def test_navigation_twin_has_state_config_behavior_and_separate_logs(tmp_path):
    config = NavigationMissionConfig(
        mission_id="mission-a", run_id="run-a", target_id="pipe-1", target_type="pipe",
        duration_s=10.0, timestep_s=0.25, commanded_speed_mps=1.0,
        start_xyz=(0.0, -2.0, 0.0), target_xyz=(0.0, -2.0, 3.0),
        current_xyz_mps=(0.0, 0.0, 0.05), frame_reference="failure.png",
        scenario_id="scenario-a",
    )
    run = simulate_navigation(config)
    assert run.metrics["reached_capture_distance"] is True
    assert run.frames[0].scenario_id == "scenario-a"
    assert any(event.event_type == "frame_captured" for event in run.events)
    paths = write_navigation_bundle(
        tmp_path / "navigation", states=run.states, frames=run.frames,
        targets=run.targets, events=run.events,
    )
    assert set(paths) == {
        "robot_states", "sensor_frames", "inspection_targets", "mission_events",
    }
    assert all(path.exists() and path.stat().st_size for path in paths.values())


def test_two_twin_demo_links_all_ids_and_fails_safe_without_model1(tmp_path):
    pytest.importorskip("PIL")
    root = __import__("pathlib").Path(__file__).resolve().parents[2]
    result = run_demo(
        navigation_config_path=root / "configs/navigation_twin/demo_mission.json",
        failure_config_path=root / "configs/failure_twin/demo_scenario.json",
        output_dir=tmp_path / "demo", run_id="run-demo", git_commit="fixture-commit",
        branch="fixture-branch", operator_or_agent="pytest",
    )
    trace = result["traceability"]
    assert all(trace[field] for field in
               ("mission_id", "frame_id", "target_id", "scenario_id", "run_id"))
    assert result["prediction"]["model_name"] == "placeholder_no_frozen_model1"
    assert result["decision"]["decision"] == "flag_unknown"
    assert (tmp_path / "demo/run_manifest.json").exists()
    assert (tmp_path / "demo/navigation_twin/robot_states.jsonl").exists()


def test_mission_decision_changes_viewpoint_and_never_returns_raw_control():
    target = InspectionTarget("pipe-1", "pipe", {}, {"angle_deg": 70.0}, 1.0, "started")
    request = MissionDecisionInput(
        "mission-1", "frame-1", RobotPose(0, 0, -1, 0, 0, 0), target,
        [{"frame_id": "frame-1", "confidence": 0.9}], [], {"entropy": 0.1},
        {"visibility": "clear"},
    )
    result = decide_mission(request)
    assert result.decision == "change_viewpoint"
    serialized = json.dumps(result.__dict__).lower()
    assert all(term not in serialized for term in ("pwm", "thruster_force", "motor_voltage"))


def test_mission_decision_input_rejects_hidden_actuator_authority():
    target = InspectionTarget("pipe-1", "pipe", {}, {"angle_deg": 0.0}, 1.0, "started")
    with pytest.raises(ValueError, match="raw actuator"):
        MissionDecisionInput(
            "m", "f", RobotPose(0, 0, 0, 0, 0, 0), target,
            [{"confidence": 0.8, "individual_thruster_force": [1.0]}], [], {}, {},
        )


def test_run_manifest_requires_limitations_and_round_trips(tmp_path):
    fields = {
        "run_id": "run-1", "date": "2026-08-25T00:00:00+03:00", "git_commit": "abc123",
        "branch": "codex/test", "operator_or_agent": "test", "track": "model2_research",
        "config_path": "config/model2.json", "dataset_manifest": "data/manifest.jsonl",
        "checkpoint_or_prototype_version": "v0.1", "inputs": ["input.json"],
        "outputs": ["output.json"], "metrics": {}, "synthetic_or_real_or_mixed": "synthetic",
        "limitations": ["fixture only"], "next_actions": ["evaluate"],
    }
    manifest = RunManifest(**fields)
    path = write_run_manifest(manifest, tmp_path / "run.json")
    assert read_run_manifest(path) == manifest
    fields["limitations"] = []
    with pytest.raises(ValueError, match="limitations"):
        RunManifest(**fields)


def test_prediction_contract_rejects_unbounded_confidence():
    with pytest.raises(ValueError, match="confidence"):
        PredictionRecord("r", "m", "v", "f", "class", "crack", 1.2)
