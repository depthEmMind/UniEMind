"""Task and conversation sessions."""

from __future__ import annotations

import asyncio

from schema import Session, Status, Task


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def start(self, session_id: str) -> Session:
        async with self._lock:
            session = Session(session_id=session_id, status=Status.READY)
            self._sessions[session_id] = session
            return session.model_copy(deep=True)

    async def attach_task(self, session_id: str, task: Task) -> Session:
        async with self._lock:
            session = self._sessions.setdefault(session_id, Session(session_id=session_id))
            session.active_task_id = task.task_id
            session.history.append(task.task_id)
            session.status = Status.RUNNING
            session.working_context["goal"] = task.goal
            self._sessions[session_id] = session
            return session.model_copy(deep=True)

    async def get(self, session_id: str) -> Session | None:
        async with self._lock:
            session = self._sessions.get(session_id)
            return session.model_copy(deep=True) if session else None
