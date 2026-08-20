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

from schema.base import UniEMindModel, utc_now
from schema.memory import MemoryContext, MemorySnippet


class MemoryKind(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    CAPABILITY = "capability"
    SYSTEM_STATE = "system_state"


LONG_TERM_KINDS: frozenset[MemoryKind] = frozenset(
    {MemoryKind.EPISODIC, MemoryKind.SEMANTIC, MemoryKind.CAPABILITY, MemoryKind.SYSTEM_STATE}
)


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

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._records)
            self._records.clear()
            return count

    async def dump(self) -> list[MemoryRecord]:
        async with self._lock:
            return [record.model_copy(deep=True) for record in self._records.values()]


class MemoryRouter:
    """Routes retrieval and updates without exposing stores to the Agent."""

    def __init__(self, stores: dict[MemoryKind, MemoryStore] | None = None) -> None:
        self._stores = stores or {kind: InMemoryStore(kind) for kind in MemoryKind}

    async def remember(self, record: MemoryRecord) -> None:
        await self._stores[record.kind].add(record)

    async def update(self, record: MemoryRecord) -> None:
        await self.remember(record)

    async def query(self, query: MemoryQuery) -> list[MemoryRecord]:
        return await self.retrieve(query)

    async def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        kinds = query.kinds or set(MemoryKind)
        groups = await asyncio.gather(
            *(self._stores[kind].search(query) for kind in kinds if kind in self._stores)
        )
        records = [record for group in groups for record in group]
        return self.rank(records)[: query.limit]

    def rank(self, records: list[MemoryRecord]) -> list[MemoryRecord]:
        ranked = list(records)
        ranked.sort(key=lambda record: (record.relevance, record.created_at), reverse=True)
        return ranked

    async def inject(self, text: str, limit: int = 10) -> MemoryContext:
        records = await self.retrieve(
            MemoryQuery(text=text, kinds=set(LONG_TERM_KINDS), limit=max(limit * len(LONG_TERM_KINDS), 1))
        )
        grouped: dict[MemoryKind, list[MemorySnippet]] = {kind: [] for kind in LONG_TERM_KINDS}
        for record in records:
            if record.kind not in grouped or len(grouped[record.kind]) >= limit:
                continue
            grouped[record.kind].append(
                MemorySnippet(
                    kind=record.kind.value,
                    content=record.content,
                    relevance=record.relevance,
                    tags=set(record.tags),
                )
            )
        return MemoryContext(
            request=text,
            episodic=grouped[MemoryKind.EPISODIC],
            semantic=grouped[MemoryKind.SEMANTIC],
            capability=grouped[MemoryKind.CAPABILITY],
            system_state=grouped[MemoryKind.SYSTEM_STATE],
        )

    async def forget(self, kind: MemoryKind, memory_id: UUID) -> bool:
        return await self._stores[kind].forget(memory_id)

    async def dump(self) -> list[MemoryRecord]:
        groups = await asyncio.gather(
            *(store.dump() for store in self._stores.values() if hasattr(store, "dump"))
        )
        return [record for group in groups for record in group]

    async def consolidate_working(self) -> int:
        working = self._stores[MemoryKind.WORKING]
        if not hasattr(working, "dump"):
            return 0
        records = await working.dump()
        moved = 0
        for record in records:
            episode = record.model_copy(
                update={"kind": MemoryKind.EPISODIC, "tags": set(record.tags) | {"consolidated"}}
            )
            await self._stores[MemoryKind.EPISODIC].add(episode)
            await working.forget(record.memory_id)
            moved += 1
        return moved

    async def consolidate(self) -> int:
        return await self.consolidate_working()
