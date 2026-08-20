from pathlib import Path

from config import load_config
from schema import RobotProfile


def test_load_robot_profile_with_overrides(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "robot.yaml"
    path.write_text("name: test\ntype: mobile\n", encoding="utf-8")
    monkeypatch.setenv("UNIEMIND_FRAME_ID", "odom")
    profile = load_config(path, RobotProfile, overrides={"capabilities": ["navigation"]})
    assert profile.frame_id == "odom"
    assert profile.capabilities == {"navigation"}
