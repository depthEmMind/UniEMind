"""Action requests crossing the mandatory safety boundary."""

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from uniemind.schema.base import ErrorDetail, Status, UniEMindModel


class ActionType(str, Enum):
    TOPIC = "topic"
    SERVICE = "service"
    ROS_ACTION = "action"
    CONTROLLER = "controller"


class ActionRequest(UniEMindModel):
    action_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    execution_id: UUID
    action_type: ActionType
    target: str
    command: dict[str, Any]
    timeout_seconds: float = Field(default=30.0, gt=0)
    requires_safety_check: bool = True


class ActionResult(UniEMindModel):
    action_id: UUID
    status: Status
    feedback: dict[str, Any] = Field(default_factory=dict)
    error: ErrorDetail | None = None
