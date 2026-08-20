"""Task/trace/span identifiers used by logging and monitoring."""

from __future__ import annotations

from uuid import UUID, uuid4

from schema.base import UniEMindModel


class TraceContext(UniEMindModel):
    task_id: UUID
    trace_id: UUID
    span_id: UUID
    session_id: str | None = None

    @classmethod
    def start(cls, task_id: UUID, session_id: str | None = None) -> TraceContext:
        return cls(task_id=task_id, trace_id=uuid4(), span_id=uuid4(), session_id=session_id)

    def child(self) -> TraceContext:
        return self.model_copy(update={"span_id": uuid4()})
