"""System, task, and action health monitoring."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pydantic import Field

from schema.base import Status, UniEMindModel, utc_now


class HealthRecord(UniEMindModel):
    name: str
    status: Status = Status.UNKNOWN
    updated_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


class HealthMonitor:
    def __init__(self) -> None:
        self._records: dict[str, HealthRecord] = {}
        self._lock = asyncio.Lock()
        self._watchdogs: dict[str, Callable[[], Status]] = {}

    async def report(self, name: str, status: Status, **details: Any) -> HealthRecord:
        record = HealthRecord(name=name, status=status, details=details)
        async with self._lock:
            self._records[name] = record
        return record

    async def get(self, name: str) -> HealthRecord | None:
        async with self._lock:
            record = self._records.get(name)
            return record.model_copy(deep=True) if record else None

    async def snapshot(self) -> dict[str, HealthRecord]:
        async with self._lock:
            return {name: record.model_copy(deep=True) for name, record in self._records.items()}

    def register_watchdog(self, name: str, check: Callable[[], Status]) -> None:
        self._watchdogs[name] = check

    async def tick_watchdogs(self) -> dict[str, Status]:
        results: dict[str, Status] = {}
        for name, check in self._watchdogs.items():
            status = check()
            results[name] = status
            await self.report(name, status)
        return results

    async def overall(self) -> Status:
        async with self._lock:
            statuses = [record.status for record in self._records.values()]
        if not statuses:
            return Status.UNKNOWN
        if Status.EMERGENCY_STOP in statuses:
            return Status.EMERGENCY_STOP
        if Status.FAILED in statuses:
            return Status.FAILED
        if Status.TIMEOUT in statuses:
            return Status.TIMEOUT
        if Status.WARNING in statuses:
            return Status.WARNING
        if all(status == Status.SUCCESS for status in statuses):
            return Status.SUCCESS
        if Status.RUNNING in statuses:
            return Status.RUNNING
        return Status.READY
