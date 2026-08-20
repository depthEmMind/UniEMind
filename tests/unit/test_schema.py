from uuid import uuid4

import pytest
from pydantic import ValidationError

from schema import (
    ActionRequest,
    ActionType,
    Header,
    ObservedObject,
    RobotState,
    SensorData,
    SensorDataType,
    WorldState,
)


def test_sensor_data_round_trip() -> None:
    data = SensorData(
        header=Header(source="front_camera", frame_id="camera_link", sequence=42),
        sensor_id="camera_front",
        data_type=SensorDataType.IMAGE,
        payload={"width": 640, "height": 480},
    )
    restored = SensorData.model_validate_json(data.model_dump_json())
    assert restored == data


def test_schema_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Header(source="camera", unsupported=True)  # type: ignore[call-arg]


def test_action_requires_safety_by_default() -> None:
    action = ActionRequest(
        task_id=uuid4(),
        execution_id=uuid4(),
        action_type=ActionType.ROS_ACTION,
        target="/navigate_to_pose",
        command={"frame_id": "map"},
    )
    assert action.requires_safety_check is True


def test_world_state_uses_object_identity() -> None:
    cup = ObservedObject(object_id="cup-1", label="cup", confidence=0.96)
    state = WorldState(objects={cup.object_id: cup})
    assert state.objects["cup-1"].label == "cup"


def test_robot_state_has_versioned_header() -> None:
    state = RobotState(header=Header(source="robot"))
    assert state.header.schema_version == "v1"
