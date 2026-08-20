"""Multi-layer memory system: areas, persistence, routing, and consolidation."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from memory.areas import (
    CapabilityMemoryArea,
    EpisodicMemoryArea,
    SemanticMemoryArea,
    SystemStateMemoryArea,
    WorkingMemoryArea,
)
from memory.config import MemoryConfig
from memory.consolidation import ConsolidationEngine, ConsolidationReport, LLMSummarizer, TokenEstimator
from memory.core import LONG_TERM_KINDS, MemoryKind, MemoryQuery, MemoryRecord, MemoryRouter
from memory.persist import MemoryFileStore
from schema.memory import (
    EventTrajectory,
    MemoryContext,
    MemorySnippet,
    SceneObject,
    TaskNode,
)


class MultiLayerMemorySystem:
    def __init__(
        self,
        root: str | Path,
        config: MemoryConfig | None = None,
        *,
        llm: LLMSummarizer | None = None,
        router: MemoryRouter | None = None,
    ) -> None:
        self.config = config or MemoryConfig()
        self.store = MemoryFileStore(root)
        self.working = WorkingMemoryArea(self.config)
        self.episodic = EpisodicMemoryArea(self.config)
        self.semantic = SemanticMemoryArea(self.config)
        self.capability = CapabilityMemoryArea(self.config)
        self.system_state = SystemStateMemoryArea(self.config)
        self.router = router or MemoryRouter()
        self.engine = ConsolidationEngine(llm=llm, keep_recent=self.config.episodic_keep_recent)
        self.estimator = TokenEstimator()

    async def load(self) -> None:
        nodes = self.store.load_working()
        await self.working.load(nodes)
        events, summary = self.store.load_episodic()
        await self.episodic.load(events, summary)
        await self.semantic.load(self.store.load_semantic())
        await self.capability.load(self.store.load_capability())
        history, stats, availability = self.store.load_system_state()
        await self.system_state.load(history, stats, availability)
        await self._reindex()

    async def persist(self) -> None:
        sessions: dict[str, list[TaskNode]] = {}
        for node in await self.working.list_tasks():
            sessions.setdefault(node.session_id, []).append(node)
        known = set(sessions)
        if self.store.working_dir.exists():
            known.update(path.stem for path in self.store.working_dir.glob("*.jsonl"))
        for session_id in known:
            self.store.save_working(session_id, sessions.get(session_id, []))
        self.store.save_episodic(await self.episodic.dump(), await self.episodic.latest_scene())
        self.store.save_semantic(await self.semantic.dump())
        self.store.save_capability(await self.capability.dump())
        await self.persist_system_state()

    async def persist_system_state(self) -> None:
        self.store.save_system_state(
            await self.system_state.dump_events(),
            await self.system_state.dump_stats(),
            await self.system_state.dump_availability(),
        )

    async def handle_request(
        self,
        request: str,
        *,
        session_id: str,
        task_id: str,
        pending_steps: list[dict[str, Any]] | None = None,
    ) -> MemoryContext:
        context = await self.assemble_context(request)
        node = await self.working.update(
            session_id=session_id,
            task_id=task_id,
            user_request=request,
            pending_steps=pending_steps,
            status="running",
        )
        await self._index(
            MemoryKind.WORKING,
            node.model_dump(mode="json"),
            {session_id, task_id, "working"},
        )
        self.store.save_working(session_id, await self.working.list_tasks(session_id))
        return context

    async def update_working(self, **kwargs: Any) -> TaskNode:
        node = await self.working.update(**kwargs)
        await self._index(MemoryKind.WORKING, node.model_dump(mode="json"), {node.session_id, node.task_id})
        return node

    async def append_episode(self, event: EventTrajectory) -> EventTrajectory:
        stored = await self.episodic.append(event)
        await self._index(MemoryKind.EPISODIC, stored.model_dump(mode="json"), {stored.event, stored.node})
        return stored

    async def upsert_object(self, obj: SceneObject) -> SceneObject:
        stored = await self.semantic.upsert(obj)
        await self._index(MemoryKind.SEMANTIC, stored.model_dump(mode="json"), {stored.name, stored.location})
        return stored

    async def record_tool(self, tool: str, success: bool, **kwargs: Any) -> None:
        event = await self.system_state.record_tool(tool, success, **kwargs)
        await self._index(MemoryKind.SYSTEM_STATE, event.model_dump(mode="json"), {tool, event.component})
        await self.persist_system_state()

    async def assemble_context(self, request: str, limit: int | None = None) -> MemoryContext:
        per_layer = limit or self.config.inject_limit
        episodic = await self.episodic.query(text=request, limit=per_layer)
        semantic = await self.semantic.query(text=request, limit=per_layer)
        capability = await self.capability.query(text=request, limit=per_layer)
        system_events = await self.system_state.query_events(text=request, limit=per_layer)
        unavailable = await self.system_state.unavailable_tools()
        snippets_capability = [
            MemorySnippet(kind=MemoryKind.CAPABILITY.value, content=_jsonable(item), tags={key})
            for key, values in capability.items()
            for item in (values if isinstance(values, list) else [values])
        ][:per_layer]
        system_snippets = [
            MemorySnippet(kind=MemoryKind.SYSTEM_STATE.value, content=item.model_dump(mode="json"), tags={item.name})
            for item in system_events
        ]
        system_snippets.extend(
            MemorySnippet(
                kind=MemoryKind.SYSTEM_STATE.value,
                content=item.model_dump(mode="json"),
                tags={item.tool, "unavailable"},
            )
            for item in unavailable
        )
        context = MemoryContext(
            request=request,
            episodic=[
                MemorySnippet(kind=MemoryKind.EPISODIC.value, content=item.model_dump(mode="json"), tags={item.event})
                for item in episodic
            ],
            semantic=[
                MemorySnippet(kind=MemoryKind.SEMANTIC.value, content=item.model_dump(mode="json"), tags={item.name})
                for item in semantic
            ],
            capability=snippets_capability,
            system_state=system_snippets[:per_layer],
        )
        ranked = await self.router.inject(request, limit=per_layer)
        if any((context.episodic, context.semantic, context.capability, context.system_state)):
            return context
        return ranked

    async def finish_task(self, task_id: str, *, summary: str, consolidate: bool = True) -> int:
        node = await self.working.get(task_id)
        if node is None:
            return 0
        await self.append_episode(
            EventTrajectory(
                event="task_finished",
                node="finish",
                description=summary,
                scene_state={"user_request": node.user_request, "results": node.intermediate_results},
                task_id=task_id,
            )
        )
        await self.episodic.set_summary(summary, task_id=task_id)
        moved = 0
        if consolidate:
            moved = await self.router.consolidate_working()
        await self.working.clear(task_id)
        await self.persist()
        return moved

    async def forget(self) -> dict[str, int]:
        result = {
            "episodic": await self.episodic.forget(),
            "semantic": await self.semantic.forget(),
            "capability": await self.capability.forget(),
            "system_state": await self.system_state.forget(),
        }
        await self.persist()
        return result

    async def consolidate(self) -> ConsolidationReport:
        return await self.engine.maybe_consolidate(self)

    def consolidate_later(self) -> asyncio.Task[ConsolidationReport]:
        return asyncio.create_task(self.consolidate())

    async def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        if not query.kinds:
            query = query.model_copy(update={"kinds": set(LONG_TERM_KINDS)})
        return await self.router.retrieve(query)

    async def _index(self, kind: MemoryKind, content: dict[str, Any], tags: set[str]) -> None:
        await self.router.remember(MemoryRecord(kind=kind, content=content, tags={tag for tag in tags if tag}))

    async def _reindex(self) -> None:
        for node in await self.working.list_tasks():
            await self._index(MemoryKind.WORKING, node.model_dump(mode="json"), {node.task_id, node.session_id})
        for event in await self.episodic.dump():
            await self._index(MemoryKind.EPISODIC, event.model_dump(mode="json"), {event.event, event.node})
        scene = await self.semantic.dump()
        for obj in scene.objects:
            await self._index(MemoryKind.SEMANTIC, obj.model_dump(mode="json"), {obj.name, obj.location})
        snapshot = await self.capability.dump()
        await self._index(MemoryKind.CAPABILITY, snapshot.project.model_dump(mode="json"), {"project"})
        await self._index(
            MemoryKind.CAPABILITY,
            snapshot.robot.model_dump(mode="json"),
            {"robot", *snapshot.robot.skills},
        )
        for operation in snapshot.operations:
            await self._index(MemoryKind.CAPABILITY, operation.model_dump(mode="json"), {operation.product})
        for stats in await self.system_state.dump_stats():
            await self._index(MemoryKind.SYSTEM_STATE, stats.model_dump(mode="json"), {stats.tool})


def _jsonable(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        dumped = item.model_dump(mode="json")
        return dumped if isinstance(dumped, dict) else {"value": dumped}
    if isinstance(item, dict):
        return item
    return {"value": item}


def create_memory_system(
    root: str | Path,
    config: MemoryConfig | None = None,
    llm: LLMSummarizer | None = None,
) -> MultiLayerMemorySystem:
    return MultiLayerMemorySystem(root, config, llm=llm)
