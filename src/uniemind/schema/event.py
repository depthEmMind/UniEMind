"""Observable event and structured log protocols."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from uniemind.schema.base import Status, UniEMindModel, utc_now


class Event(UniEMindModel):
    timestamp: datetime = Field(default_factory=utc_now)
    module: str
    event: str
    status: Status
    task_id: UUID | None = None
    session_id: str | None = None
    trace_id: UUID = Field(default_factory=uuid4)
    span_id: UUID = Field(default_factory=uuid4)
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    error: str | None = None
