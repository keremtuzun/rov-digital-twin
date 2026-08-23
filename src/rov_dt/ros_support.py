"""ROS-independent startup helpers so missing model failures are testable and explicit."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


def resolve_model_path(parameter_value: str, environment: Mapping[str, str] | None = None) -> Path:
    """Resolve an explicit ROS parameter first, then ROV_DT_MODEL_PATH; never invent a model."""
    env = os.environ if environment is None else environment
    requested = parameter_value.strip() or env.get("ROV_DT_MODEL_PATH", "").strip()
    if not requested:
        raise FileNotFoundError(
            "No diagnostic model configured. Set ROS parameter 'model_path' or ROV_DT_MODEL_PATH; "
            "the repository does not contain a trained model by default."
        )
    path = Path(requested).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Diagnostic model does not exist: {path}")
    return path
