import json
from pathlib import Path


def test_unity_runtime_profiles_cover_progressive_water_conditions():
    root = Path(__file__).resolve().parents[2]
    payload = json.loads(
        (root / "unity/Assets/ROVDigitalTwin/Resources/domain_randomization_profiles.json").read_text()
    )
    names = [profile["name"] for profile in payload["profiles"]]
    assert names == ["nominal", "pool", "sheltered_water", "moderate_sea", "difficult_sea"]
    assert payload["profiles"][0]["wave_height_max"] < payload["profiles"][-1]["wave_height_max"]
