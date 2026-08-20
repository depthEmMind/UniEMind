"""Task and session working-context protocols."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from schema.base import Status, UniEMindModel, utc_now
from schema.task import Task


class Session(UniEMindModel):
    session_id: str
    created_at: datetime = Field(default_factory=utc_now)
    status: Status = Status.READY
    working_context: dict[str, Any] = Field(default_factory=dict)
    active_task_id: UUID | None = None
    history: list[UUID] = Field(default_factory=list)


class WorkingContext(UniEMindModel):
    session: Session
    task: Task | None = None
    last_skill: str | None = None
    last_outputs: dict[str, Any] = Field(default_factory=dict)
