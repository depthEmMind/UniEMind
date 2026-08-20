"""Hardware-agnostic sensor data protocols."""

from enum import Enum
from typing import Any

from pydantic import Field

from schema.base import Header, UniEMindModel
from schema.geometry import Quaternion, Vector3


class SensorDataType(str, Enum):
    IMAGE = "image"
    DEPTH = "depth"
    POINT_CLOUD = "point_cloud"
    IMU = "imu"
    LASER_SCAN = "laser_scan"
    ULTRASONIC = "ultrasonic"
    JOINT_STATE = "joint_state"
    ROBOT_STATE = "robot_state"
    POSE = "pose"
    FORCE = "force"
    TACTILE = "tactile"


class SensorMetadata(UniEMindModel):
    encoding: str | None = None
    resolution: tuple[int, int] | None = None
    fps: float | None = Field(default=None, gt=0)
    intrinsics: list[float] | None = None
    extrinsics: list[float] | None = None
    noise: dict[str, float] = Field(default_factory=dict)
    calibration: dict[str, Any] = Field(default_factory=dict)


class SensorData(UniEMindModel):
    header: Header
    sensor_id: str
    data_type: SensorDataType
    payload: Any
    metadata: SensorMetadata = Field(default_factory=SensorMetadata)


class ImagePayload(UniEMindModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    encoding: str
    step: int = Field(gt=0)
    data: bytes


class IMUPayload(UniEMindModel):
    orientation: Quaternion = Field(default_factory=Quaternion)
    angular_velocity: Vector3 = Field(default_factory=Vector3)
    linear_acceleration: Vector3 = Field(default_factory=Vector3)


class LaserScanPayload(UniEMindModel):
    angle_min: float
    angle_max: float
    angle_increment: float = Field(gt=0)
    range_min: float = Field(ge=0)
    range_max: float = Field(gt=0)
    ranges: list[float]
    intensities: list[float] = Field(default_factory=list)
