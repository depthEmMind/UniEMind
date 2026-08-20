"""Observation and world-state protocols."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from schema.base import Header, UniEMindModel, utc_now
from schema.geometry import Pose, Vector3
from schema.robot import RobotState


class BoundingBox2D(UniEMindModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class ObservedObject(UniEMindModel):
    object_id: str
    label: str
    confidence: float = Field(ge=0, le=1)
    pose: Pose | None = None
    bounding_box: BoundingBox2D | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class Observation(UniEMindModel):
    header: Header
    observation_id: UUID = Field(default_factory=uuid4)
    observer: str
    objects: list[ObservedObject] = Field(default_factory=list)
    free_space: list[Vector3] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class SpatialRelation(UniEMindModel):
    subject_id: str
    relation: str
    object_id: str
    confidence: float = Field(default=1.0, ge=0, le=1)


class WorldState(UniEMindModel):
    timestamp: datetime = Field(default_factory=utc_now)
    frame_id: str = "world"
    revision: int = Field(default=0, ge=0)
    robot: RobotState | None = None
    objects: dict[str, ObservedObject] = Field(default_factory=dict)
    locations: dict[str, Pose] = Field(default_factory=dict)
    relations: list[SpatialRelation] = Field(default_factory=list)
    obstacles: list[Vector3] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
