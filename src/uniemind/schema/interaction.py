"""User interaction request and response protocols."""

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from uniemind.schema.base import ErrorDetail, Status, UniEMindModel, utc_now
from datetime import datetime


class InteractionType(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    API = "api"
    ROS2_REMOTE = "ros2_remote"


class InteractionRequest(UniEMindModel):
    session_id: str
    request_id: UUID = Field(default_factory=uuid4)
    type: InteractionType
    timestamp: datetime = Field(default_factory=utc_now)
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionResponse(UniEMindModel):
    session_id: str
    request_id: UUID
    status: Status
    content: str = ""
    error: ErrorDetail | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
