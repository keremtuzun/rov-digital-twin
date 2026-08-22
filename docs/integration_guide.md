# Burak integration guide

## Install and run

```powershell
python -m pip install -e ".[api]"
$env:OCEANSENSE_DOMAIN_CHECKPOINT = "models/oceansense_domain_efficientnet_b0.pt"
$env:OCEANSENSE_CONDITION_CHECKPOINT = "models/oceansense_condition_efficientnet_b0.pt"
# Optional only after detector training:
# $env:OCEANSENSE_DETECTOR_CHECKPOINT = "models/weak_point_yolov8n.pt"
python scripts/run_api.py
```

The API listens on `127.0.0.1:8000`. Keep the service on a private robot network and place authentication,
rate limiting, path restrictions, and TLS at the integration gateway before deployment.

## Perception request

`POST /api/perception/analyze`

```json
{
  "frame_id": "frame_00042",
  "image_path": "frames/frame_00042.jpg",
  "mission_context": {"visibility_level": "moderate", "depth_m": 4.5, "survey_goal": "structure"}
}
```

## Decision request

`POST /api/agent/decide` accepts the perception output under `perception_output` plus:

```json
{
  "mission_context": {
    "visibility_level": "moderate",
    "depth_m": 4.5,
    "battery_level": 0.82,
    "communication_status": "stable",
    "operator_mode": "semi_autonomous",
    "survey_goal": "structure"
  }
}
```

Treat `control_instruction` as a request to Burak's separately tested control layer, never as actuator
values. The control layer remains responsible for feasibility, collision avoidance, duty constraints,
operator authority, and failsafe behavior.
