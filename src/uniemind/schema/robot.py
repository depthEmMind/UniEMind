"""Robot state and profile schemas."""

from typing import Any

from pydantic import Field

from uniemind.schema.base import Header, Status, UniEMindModel
from uniemind.schema.geometry import Pose, Twist


class JointState(UniEMindModel):
    names: list[str]
    positions: list[float]
    velocities: list[float] = Field(default_factory=list)
    efforts: list[float] = Field(default_factory=list)


class RobotHealth(UniEMindModel):
    status: Status = Status.UNKNOWN
    battery_percent: float | None = Field(default=None, ge=0, le=100)
    temperatures_celsius: dict[str, float] = Field(default_factory=dict)
    faults: list[str] = Field(default_factory=list)


class RobotState(UniEMindModel):
    header: Header
    pose: Pose = Field(default_factory=Pose)
    velocity: Twist = Field(default_factory=Twist)
    joints: JointState | None = None
    end_effectors: dict[str, Pose] = Field(default_factory=dict)
    grippers: dict[str, float] = Field(default_factory=dict)
    controller_state: Status = Status.UNKNOWN
    health: RobotHealth = Field(default_factory=RobotHealth)


class RobotProfile(UniEMindModel):
    name: str
    type: str
    frame_id: str = "base_link"
    arms: dict[str, bool] = Field(default_factory=dict)
    hands: dict[str, str] = Field(default_factory=dict)
    sensors: dict[str, bool] = Field(default_factory=dict)
    capabilities: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)
