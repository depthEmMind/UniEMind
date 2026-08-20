"""Five-layer memory interfaces, in-memory stores, and routing."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from uniemind.schema.base import UniEMindModel, utc_now


class MemoryKind(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    CAPABILITY = "capability"
    SYSTEM_STATE = "system_state"


class MemoryRecord(UniEMindModel):
    memory_id: UUID = Field(default_factory=uuid4)
    kind: MemoryKind
    content: dict[str, Any]
    tags: set[str] = Field(default_factory=set)
    created_at: datetime = Field(default_factory=utc_now)
    relevance: float = Field(default=1.0, ge=0, le=1)


class MemoryQuery(UniEMindModel):
    text: str = ""
    kinds: set[MemoryKind] = Field(default_factory=lambda: set(MemoryKind))
    tags: set[str] = Field(default_factory=set)
    limit: int = Field(default=10, gt=0, le=100)


class MemoryStore(ABC):
    @abstractmethod
    async def add(self, record: MemoryRecord) -> None: ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemoryRecord]: ...

    @abstractmethod
    async def forget(self, memory_id: UUID) -> bool: ...


class InMemoryStore(MemoryStore):
    def __init__(self, kind: MemoryKind) -> None:
        self.kind = kind
        self._records: dict[UUID, MemoryRecord] = {}
        self._lock = asyncio.Lock()

    async def add(self, record: MemoryRecord) -> None:
        if record.kind != self.kind:
            raise ValueError(f"{record.kind} cannot be added to {self.kind} store")
        async with self._lock:
            self._records[record.memory_id] = record.model_copy(deep=True)

    async def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        needle = query.text.casefold()
        async with self._lock:
            matches = [
                record.model_copy(deep=True)
                for record in self._records.values()
                if record.kind in query.kinds
                and query.tags.issubset(record.tags)
                and (not needle or needle in json.dumps(record.content, default=str).casefold())
            ]
        matches.sort(key=lambda record: (record.relevance, record.created_at), reverse=True)
        return matches[: query.limit]

    async def forget(self, memory_id: UUID) -> bool:
        async with self._lock:
            return self._records.pop(memory_id, None) is not None


class MemoryRouter:
    """Routes retrieval and updates without exposing stores to the Agent."""

    def __init__(self, stores: dict[MemoryKind, MemoryStore] | None = None) -> None:
        self._stores = stores or {kind: InMemoryStore(kind) for kind in MemoryKind}

    async def remember(self, record: MemoryRecord) -> None:
        await self._stores[record.kind].add(record)

    async def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        groups = await asyncio.gather(
            *(self._stores[kind].search(query) for kind in query.kinds if kind in self._stores)
        )
        records = [record for group in groups for record in group]
        records.sort(key=lambda record: (record.relevance, record.created_at), reverse=True)
        return records[: query.limit]

    async def forget(self, kind: MemoryKind, memory_id: UUID) -> bool:
        return await self._stores[kind].forget(memory_id)
