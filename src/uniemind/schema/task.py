"""Task and plan protocols."""

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from uniemind.schema.base import Status, UniEMindModel


class TaskStepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskStep(UniEMindModel):
    step_id: UUID = Field(default_factory=uuid4)
    name: str
    skill: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    status: TaskStepStatus = TaskStepStatus.PENDING
    error: str | None = None


class Task(UniEMindModel):
    task_id: UUID = Field(default_factory=uuid4)
    session_id: str
    goal: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    steps: list[TaskStep] = Field(default_factory=list)
    status: Status = Status.INITIALIZING
    current_step: int | None = Field(default=None, ge=0)
