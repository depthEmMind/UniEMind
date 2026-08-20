"""Coordinate-frame-aware geometry schemas."""

from pydantic import Field, model_validator

from schema.base import UniEMindModel


class Vector3(UniEMindModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Quaternion(UniEMindModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0

    @model_validator(mode="after")
    def validate_nonzero(self) -> "Quaternion":
        norm_sq = self.x**2 + self.y**2 + self.z**2 + self.w**2
        if norm_sq == 0:
            raise ValueError("quaternion must not be zero")
        return self


class Pose(UniEMindModel):
    position: Vector3 = Field(default_factory=Vector3)
    orientation: Quaternion = Field(default_factory=Quaternion)
    frame_id: str = "world"


class Twist(UniEMindModel):
    linear: Vector3 = Field(default_factory=Vector3)
    angular: Vector3 = Field(default_factory=Vector3)
