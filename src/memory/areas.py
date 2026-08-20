"""Typed memory areas for the five-layer tree."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from memory.config import MemoryConfig
from schema.base import utc_now
from schema.memory import (
    BehaviorNorm,
    CapabilitySnapshot,
    EventTrajectory,
    OperationHabit,
    ProductOperation,
    ProjectInfo,
    RobotCapability,
    SceneMap,
    SceneObject,
    SceneSummary,
    SystemEvent,
    TaskNode,
    ToolAvailability,
    ToolStats,
)

_LATIN_RE = re.compile(r"[A-Za-z0-9_]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _tokens(text: str) -> list[str]:
    tokens = [token for token in _LATIN_RE.findall(text) if len(token) >= 2]
    cjk = "".join(_CJK_RE.findall(text))
    tokens.extend(cjk[index : index + 2] for index in range(max(len(cjk) - 1, 0)))
    return tokens


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return True
    blob = haystack.casefold()
    if needle.casefold() in blob:
        return True
    return any(token.casefold() in blob for token in _tokens(needle))


class WorkingMemoryArea:
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()
        self._tasks: dict[str, TaskNode] = {}
        self._lock = asyncio.Lock()

    async def update(
        self,
        *,
        session_id: str,
        task_id: str,
        user_request: str | None = None,
        pending_steps: list[dict[str, Any]] | None = None,
        result: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> TaskNode:
        async with self._lock:
            node = self._tasks.get(task_id) or TaskNode(session_id=session_id, task_id=task_id)
            if user_request is not None:
                node.user_request = user_request
            if pending_steps is not None:
                node.pending_steps = list(pending_steps)
            if result is not None:
                node.intermediate_results.append(result)
                overflow = len(node.intermediate_results) - self.config.working_limit
                if overflow > 0:
                    node.intermediate_results = node.intermediate_results[overflow:]
            if status is not None:
                node.status = status
            node.session_id = session_id
            node.updated_at = utc_now()
            self._tasks[task_id] = node
            return node.model_copy(deep=True)

    async def get(self, task_id: str) -> TaskNode | None:
        async with self._lock:
            node = self._tasks.get(task_id)
            return node.model_copy(deep=True) if node else None

    async def list_tasks(self, session_id: str | None = None) -> list[TaskNode]:
        async with self._lock:
            nodes = list(self._tasks.values())
            if session_id is not None:
                nodes = [node for node in nodes if node.session_id == session_id]
            return [node.model_copy(deep=True) for node in nodes]

    async def clear(self, task_id: str | None = None) -> int:
        async with self._lock:
            if task_id is None:
                count = len(self._tasks)
                self._tasks.clear()
                return count
            return 1 if self._tasks.pop(task_id, None) is not None else 0

    async def load(self, nodes: list[TaskNode]) -> int:
        async with self._lock:
            for node in nodes:
                self._tasks[node.task_id] = node.model_copy(deep=True)
            return len(nodes)


class EpisodicMemoryArea:
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()
        self._events: list[EventTrajectory] = []
        self.summary = SceneSummary()
        self._lock = asyncio.Lock()

    async def append(self, event: EventTrajectory) -> EventTrajectory:
        async with self._lock:
            stored = event.model_copy(deep=True)
            self._events.append(stored)
            return stored.model_copy(deep=True)

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._events)
            self._events.clear()
            self.summary = SceneSummary()
            return count

    async def load(self, events: list[EventTrajectory], summary: SceneSummary | None = None) -> int:
        async with self._lock:
            self._events = [event.model_copy(deep=True) for event in events]
            if summary is not None:
                self.summary = summary.model_copy(deep=True)
            return len(self._events)

    async def dump(self) -> list[EventTrajectory]:
        async with self._lock:
            return [event.model_copy(deep=True) for event in self._events]

    async def set_summary(self, text: str, task_id: str | None = None) -> SceneSummary:
        async with self._lock:
            self.summary = SceneSummary(text=text, task_id=task_id)
            return self.summary.model_copy(deep=True)

    async def latest_scene(self) -> SceneSummary:
        async with self._lock:
            return self.summary.model_copy(deep=True)

    async def query(
        self,
        *,
        event: str | None = None,
        at: datetime | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        text: str = "",
        limit: int = 20,
    ) -> list[EventTrajectory]:
        async with self._lock:
            matches = []
            for item in self._events:
                if event is not None and item.event != event:
                    continue
                if at is not None and item.timestamp != at:
                    continue
                if start is not None and item.timestamp < start:
                    continue
                if end is not None and item.timestamp > end:
                    continue
                blob = f"{item.event} {item.node} {item.description} {item.scene_state}"
                if not _contains(blob, text):
                    continue
                matches.append(item.model_copy(deep=True))
        matches.sort(key=lambda item: item.timestamp, reverse=True)
        return matches[:limit]

    async def times_of(self, event: str) -> list[datetime]:
        hits = await self.query(event=event, limit=10_000)
        return [item.timestamp for item in reversed(hits)]

    async def modify(self, event_id: UUID, **updates: Any) -> EventTrajectory:
        async with self._lock:
            for index, item in enumerate(self._events):
                if item.event_id == event_id:
                    updated = item.model_copy(update=updates)
                    self._events[index] = updated
                    return updated.model_copy(deep=True)
        raise KeyError(f"episodic event not found: {event_id}")

    async def delete_between(self, start: datetime, end: datetime) -> int:
        async with self._lock:
            keep = [item for item in self._events if not (start <= item.timestamp <= end)]
            removed = len(self._events) - len(keep)
            self._events = keep
            return removed

    async def forget(self, *, now: datetime | None = None, decay: float = 0.05) -> int:
        cutoff = self.config.confidence_forget_threshold
        moment = now or utc_now()
        removed = 0
        async with self._lock:
            kept: list[EventTrajectory] = []
            for item in self._events:
                age_days = max((moment - item.timestamp).total_seconds() / 86400.0, 0.0)
                confidence = max(item.confidence - decay * age_days, 0.0)
                if confidence < cutoff:
                    removed += 1
                    continue
                kept.append(item.model_copy(update={"confidence": confidence}))
            self._events = kept
        return removed

    async def keep_recent(self, count: int) -> list[EventTrajectory]:
        async with self._lock:
            if count < len(self._events):
                archived = [item.model_copy(deep=True) for item in self._events[:-count]]
            else:
                archived = []
            self._events = self._events[-count:]
            return archived

    async def drop_weakest(self, count: int) -> int:
        async with self._lock:
            if count <= 0 or not self._events:
                return 0
            ordered = sorted(self._events, key=lambda item: (item.confidence, item.timestamp))
            drop_ids = {item.event_id for item in ordered[:count]}
            self._events = [item for item in self._events if item.event_id not in drop_ids]
            return len(drop_ids)


class SemanticMemoryArea:
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()
        self.map = SceneMap()
        self._lock = asyncio.Lock()

    async def upsert(self, obj: SceneObject) -> SceneObject:
        async with self._lock:
            stored = obj.model_copy(deep=True)
            stored.last_seen = utc_now()
            stored.present = True
            for index, existing in enumerate(self.map.objects):
                if existing.name == stored.name:
                    merged = existing.model_copy(
                        update={
                            "location": stored.location or existing.location,
                            "description": stored.description or existing.description,
                            "relations": {**existing.relations, **stored.relations},
                            "confidence": stored.confidence,
                            "last_seen": stored.last_seen,
                            "position": stored.position if stored.position is not None else existing.position,
                            "present": True,
                        }
                    )
                    self.map.objects[index] = merged
                    return merged.model_copy(deep=True)
            self.map.objects.append(stored)
            return stored.model_copy(deep=True)

    async def load(self, scene: SceneMap) -> None:
        async with self._lock:
            self.map = scene.model_copy(deep=True)

    async def dump(self) -> SceneMap:
        async with self._lock:
            return self.map.model_copy(deep=True)

    async def load_local(self, *, location: str | None = None, names: set[str] | None = None) -> list[SceneObject]:
        async with self._lock:
            objects = []
            for item in self.map.objects:
                if location is not None and item.location != location:
                    continue
                if names is not None and item.name not in names:
                    continue
                objects.append(item.model_copy(deep=True))
            return objects

    async def clear(self) -> int:
        async with self._lock:
            count = len(self.map.objects)
            self.map = SceneMap(map_id=self.map.map_id)
            return count

    async def mark_absent(self, name: str) -> bool:
        async with self._lock:
            for index, item in enumerate(self.map.objects):
                if item.name == name:
                    self.map.objects[index] = item.model_copy(update={"present": False, "confidence": 0.0})
                    return True
            return False

    async def forget(self, *, now: datetime | None = None) -> int:
        moment = now or utc_now()
        ttl = timedelta(seconds=self.config.object_unseen_seconds)
        cutoff = self.config.confidence_forget_threshold
        changed = 0
        async with self._lock:
            updated: list[SceneObject] = []
            for item in self.map.objects:
                if item.present and moment - item.last_seen > ttl:
                    decayed = max(item.confidence * 0.5, 0.0)
                    item = item.model_copy(update={"confidence": decayed, "present": False})
                    changed += 1
                if item.confidence >= cutoff:
                    updated.append(item)
                else:
                    changed += 1
            self.map.objects = updated
        return changed

    async def query(
        self,
        *,
        name: str | None = None,
        location: str | None = None,
        relation: tuple[str, str] | None = None,
        text: str = "",
        present_only: bool = True,
        limit: int = 20,
    ) -> list[SceneObject]:
        async with self._lock:
            matches = []
            for item in self.map.objects:
                if present_only and not item.present:
                    continue
                if name is not None and item.name != name:
                    continue
                if location is not None and item.location != location:
                    continue
                if relation is not None:
                    rel, target = relation
                    if item.relations.get(rel) != target:
                        continue
                blob = f"{item.name} {item.location} {item.description} {item.relations}"
                if not _contains(blob, text):
                    continue
                matches.append(item.model_copy(deep=True))
        matches.sort(key=lambda item: (item.confidence, item.last_seen), reverse=True)
        return matches[:limit]


class CapabilityMemoryArea:
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()
        self.snapshot = CapabilitySnapshot()
        self._lock = asyncio.Lock()

    async def load(self, snapshot: CapabilitySnapshot) -> None:
        async with self._lock:
            self.snapshot = snapshot.model_copy(deep=True)

    async def dump(self) -> CapabilitySnapshot:
        async with self._lock:
            return self.snapshot.model_copy(deep=True)

    async def set_project(self, project: ProjectInfo) -> None:
        async with self._lock:
            self.snapshot.project = project.model_copy(deep=True)

    async def set_robot(self, robot: RobotCapability) -> None:
        async with self._lock:
            self.snapshot.robot = robot.model_copy(deep=True)

    async def upsert_operation(self, operation: ProductOperation) -> ProductOperation:
        async with self._lock:
            stored = operation.model_copy(deep=True)
            for index, existing in enumerate(self.snapshot.operations):
                if existing.product == stored.product:
                    self.snapshot.operations[index] = stored
                    return stored.model_copy(deep=True)
            self.snapshot.operations.append(stored)
            return stored.model_copy(deep=True)

    async def upsert_norm(self, norm: BehaviorNorm) -> BehaviorNorm:
        async with self._lock:
            stored = norm.model_copy(deep=True)
            for index, existing in enumerate(self.snapshot.norms):
                if existing.rule_id == stored.rule_id:
                    self.snapshot.norms[index] = stored
                    return stored.model_copy(deep=True)
            self.snapshot.norms.append(stored)
            return stored.model_copy(deep=True)

    async def add_habit(self, habit: OperationHabit) -> OperationHabit:
        async with self._lock:
            stored = habit.model_copy(deep=True)
            self.snapshot.habits.append(stored)
            return stored.model_copy(deep=True)

    async def clear_dynamic(self) -> int:
        async with self._lock:
            count = len(self.snapshot.operations) + len(self.snapshot.norms) + len(self.snapshot.habits)
            self.snapshot.operations = []
            self.snapshot.norms = []
            self.snapshot.habits = []
            return count

    async def forget(self) -> int:
        cutoff = self.config.habit_confidence_threshold
        async with self._lock:
            keep = [habit for habit in self.snapshot.habits if habit.confidence >= cutoff]
            removed = len(self.snapshot.habits) - len(keep)
            self.snapshot.habits = keep
            return removed

    async def modify_operation(self, product: str, **updates: Any) -> ProductOperation:
        async with self._lock:
            for index, item in enumerate(self.snapshot.operations):
                if item.product == product:
                    updated = item.model_copy(update=updates)
                    self.snapshot.operations[index] = updated
                    return updated.model_copy(deep=True)
        raise KeyError(f"product operation not found: {product}")

    async def modify_norm(self, rule_id: str, **updates: Any) -> BehaviorNorm:
        async with self._lock:
            for index, item in enumerate(self.snapshot.norms):
                if item.rule_id == rule_id:
                    updated = item.model_copy(update=updates)
                    self.snapshot.norms[index] = updated
                    return updated.model_copy(deep=True)
        raise KeyError(f"behavior norm not found: {rule_id}")

    async def delete_operation(self, product: str) -> bool:
        async with self._lock:
            before = len(self.snapshot.operations)
            self.snapshot.operations = [item for item in self.snapshot.operations if item.product != product]
            return len(self.snapshot.operations) < before

    async def delete_habit(self, habit_id: str) -> bool:
        async with self._lock:
            before = len(self.snapshot.habits)
            self.snapshot.habits = [item for item in self.snapshot.habits if item.habit_id != habit_id]
            return len(self.snapshot.habits) < before

    async def query(
        self,
        *,
        product: str | None = None,
        task_type: str | None = None,
        skills: bool = False,
        text: str = "",
        limit: int = 20,
    ) -> dict[str, Any]:
        async with self._lock:
            snapshot = self.snapshot.model_copy(deep=True)
        result: dict[str, Any] = {}
        if product is not None:
            result["operations"] = [item for item in snapshot.operations if item.product == product]
        elif task_type is not None:
            result["norms"] = [item for item in snapshot.norms if item.task_type == task_type]
        elif skills:
            result["skills"] = list(snapshot.robot.skills)
        else:
            result["operations"] = [
                item for item in snapshot.operations if _contains(f"{item.product} {item.steps}", text)
            ]
            result["norms"] = [item for item in snapshot.norms if _contains(f"{item.task_type} {item.rule}", text)]
            result["habits"] = [item for item in snapshot.habits if _contains(item.description, text)]
            result["skills"] = [name for name in snapshot.robot.skills if _contains(name, text)]
            result["project"] = snapshot.project
        for key, value in list(result.items()):
            if isinstance(value, list):
                result[key] = value[:limit]
        return result


class SystemStateMemoryArea:
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()
        self._events: list[SystemEvent] = []
        self._stats: dict[str, ToolStats] = {}
        self._availability: dict[str, ToolAvailability] = {}
        self._lock = asyncio.Lock()

    async def record_tool(
        self,
        tool: str,
        success: bool,
        *,
        component: str = "tool",
        details: dict[str, Any] | None = None,
    ) -> SystemEvent:
        async with self._lock:
            stats = self._stats.get(tool) or ToolStats(tool=tool)
            if success:
                stats = stats.model_copy(update={"successes": stats.successes + 1})
            else:
                stats = stats.model_copy(update={"failures": stats.failures + 1})
            self._stats[tool] = stats
            availability = self._availability.get(tool) or ToolAvailability(tool=tool)
            if stats.success_rate < self.config.availability_rate_threshold:
                availability = availability.model_copy(
                    update={"available": False, "reason": "success rate below threshold"}
                )
            elif availability.reason == "success rate below threshold":
                availability = availability.model_copy(update={"available": True, "reason": ""})
            self._availability[tool] = availability
            event = SystemEvent(
                component=component,
                name=tool,
                success=success,
                details=details or {},
            )
            self._events.append(event)
            return event.model_copy(deep=True)

    async def set_available(self, tool: str, available: bool, reason: str = "") -> ToolAvailability:
        async with self._lock:
            item = ToolAvailability(tool=tool, available=available, reason=reason)
            self._availability[tool] = item
            return item.model_copy(deep=True)

    async def set_stats(self, stats: ToolStats) -> None:
        async with self._lock:
            self._stats[stats.tool] = stats.model_copy(deep=True)

    async def load(
        self,
        events: list[SystemEvent],
        stats: list[ToolStats],
        availability: list[ToolAvailability],
    ) -> None:
        async with self._lock:
            self._events = [item.model_copy(deep=True) for item in events]
            self._stats = {item.tool: item.model_copy(deep=True) for item in stats}
            self._availability = {item.tool: item.model_copy(deep=True) for item in availability}

    async def dump_events(self) -> list[SystemEvent]:
        async with self._lock:
            return [item.model_copy(deep=True) for item in self._events]

    async def dump_stats(self) -> list[ToolStats]:
        async with self._lock:
            return [item.model_copy(deep=True) for item in self._stats.values()]

    async def dump_availability(self) -> list[ToolAvailability]:
        async with self._lock:
            return [item.model_copy(deep=True) for item in self._availability.values()]

    async def clear(self, *, keep_stats: bool = True) -> int:
        async with self._lock:
            count = len(self._events)
            self._events.clear()
            if not keep_stats:
                count += len(self._stats) + len(self._availability)
                self._stats.clear()
                self._availability.clear()
            return count

    async def forget(self, *, now: datetime | None = None) -> int:
        moment = now or utc_now()
        window = timedelta(seconds=self.config.event_history_window_seconds)
        async with self._lock:
            keep = [item for item in self._events if moment - item.timestamp <= window]
            removed = len(self._events) - len(keep)
            self._events = keep
            return removed

    async def query_tool(self, tool: str) -> dict[str, Any]:
        async with self._lock:
            stats = self._stats.get(tool)
            availability = self._availability.get(tool)
            return {
                "stats": stats.model_copy(deep=True) if stats else None,
                "availability": availability.model_copy(deep=True) if availability else None,
            }

    async def unavailable_tools(self) -> list[ToolAvailability]:
        async with self._lock:
            return [
                item.model_copy(deep=True)
                for item in self._availability.values()
                if not item.available
            ]

    async def query_events(
        self,
        *,
        component: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        text: str = "",
        limit: int = 20,
    ) -> list[SystemEvent]:
        async with self._lock:
            matches = []
            for item in self._events:
                if component is not None and item.component != component:
                    continue
                if start is not None and item.timestamp < start:
                    continue
                if end is not None and item.timestamp > end:
                    continue
                blob = f"{item.component} {item.name} {item.details}"
                if not _contains(blob, text):
                    continue
                matches.append(item.model_copy(deep=True))
        matches.sort(key=lambda item: item.timestamp, reverse=True)
        return matches[:limit]

    async def modify_stats(self, tool: str, **updates: Any) -> ToolStats:
        async with self._lock:
            current = self._stats.get(tool) or ToolStats(tool=tool)
            updated = current.model_copy(update=updates)
            self._stats[tool] = updated
            return updated.model_copy(deep=True)

    async def delete_tool(self, tool: str) -> bool:
        async with self._lock:
            existed = tool in self._stats or tool in self._availability
            self._stats.pop(tool, None)
            self._availability.pop(tool, None)
            self._events = [item for item in self._events if item.name != tool]
            return existed

    async def delete_events_between(self, start: datetime, end: datetime) -> int:
        async with self._lock:
            keep = [item for item in self._events if not (start <= item.timestamp <= end)]
            removed = len(self._events) - len(keep)
            self._events = keep
            return removed
