"""File persistence for layered memory and a legacy JSON archive."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from memory.core import MemoryRecord, MemoryRouter
from schema.memory import (
    BehaviorNorm,
    CapabilitySnapshot,
    EventTrajectory,
    OperationHabit,
    ProductOperation,
    ProjectInfo,
    RobotCapability,
    SceneMap,
    SceneSummary,
    SystemEvent,
    TaskNode,
    ToolAvailability,
    ToolStats,
)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    body = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    _atomic_write(path, f"# {title}\n\n```yaml\n{body}```\n")


def read_markdown(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if "```yaml" in text:
        block = text.split("```yaml", 1)[1].split("```", 1)[0]
        loaded = yaml.safe_load(block) or {}
    else:
        loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"markdown payload must be a mapping: {path}")
    return loaded


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    _atomic_write(path, text)


def write_json(path: Path, payload: Any) -> None:
    _atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False))


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


class JsonMemoryArchive:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    async def save(self, router: MemoryRouter) -> int:
        records = await router.dump()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.model_dump(mode="json") for record in records]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return len(payload)

    async def load(self, router: MemoryRouter) -> int:
        if not self.path.exists():
            return 0
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        count = 0
        for item in payload:
            await router.remember(MemoryRecord.model_validate(item))
            count += 1
        return count


class MemoryFileStore:
    """Layered files matching the memory design layout."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.working_dir = self.root / "working_memory"
        self.episodic_dir = self.root / "episodic"
        self.semantic_dir = self.root / "semantic"
        self.capability_dir = self.root / "capability"
        self.system_dir = self.root / "system_state"
        self.archive_dir = self.episodic_dir / "archive"

    @property
    def event_trajectory_path(self) -> Path:
        return self.episodic_dir / "event_trajectory.jsonl"

    @property
    def scene_summary_path(self) -> Path:
        return self.episodic_dir / "scene_summary.md"

    @property
    def scene_map_path(self) -> Path:
        return self.semantic_dir / "scene_map.md"

    @property
    def project_info_path(self) -> Path:
        return self.capability_dir / "project_info.md"

    @property
    def robot_capability_path(self) -> Path:
        return self.capability_dir / "robot_capability.md"

    @property
    def product_operations_path(self) -> Path:
        return self.capability_dir / "product_operations.md"

    @property
    def behavior_norms_path(self) -> Path:
        return self.capability_dir / "behavior_norms.md"

    @property
    def operation_habits_path(self) -> Path:
        return self.capability_dir / "operation_habits.md"

    @property
    def event_history_path(self) -> Path:
        return self.system_dir / "event_history.jsonl"

    @property
    def tool_success_rate_path(self) -> Path:
        return self.system_dir / "tool_success_rate.json"

    @property
    def tool_availability_path(self) -> Path:
        return self.system_dir / "tool_availability.json"

    def working_path(self, session_id: str) -> Path:
        return self.working_dir / f"{session_id}.jsonl"

    def save_working(self, session_id: str, nodes: list[TaskNode]) -> None:
        write_jsonl(self.working_path(session_id), [node.model_dump(mode="json") for node in nodes])

    def load_working(self, session_id: str | None = None) -> list[TaskNode]:
        paths = [self.working_path(session_id)] if session_id else sorted(self.working_dir.glob("*.jsonl"))
        nodes: list[TaskNode] = []
        for path in paths:
            for row in read_jsonl(path):
                nodes.append(TaskNode.model_validate(row))
        return nodes

    def save_episodic(self, events: list[EventTrajectory], summary: SceneSummary) -> None:
        write_jsonl(self.event_trajectory_path, [item.model_dump(mode="json") for item in events])
        write_markdown(self.scene_summary_path, "Scene Summary", summary.model_dump(mode="json"))

    def load_episodic(self) -> tuple[list[EventTrajectory], SceneSummary]:
        events = [EventTrajectory.model_validate(row) for row in read_jsonl(self.event_trajectory_path)]
        payload = read_markdown(self.scene_summary_path)
        summary = SceneSummary.model_validate(payload) if payload else SceneSummary()
        return events, summary

    def archive_events(self, name: str, events: list[EventTrajectory]) -> Path:
        path = self.archive_dir / f"{name}.jsonl"
        write_jsonl(path, [item.model_dump(mode="json") for item in events])
        return path

    def save_semantic(self, scene: SceneMap) -> None:
        write_markdown(self.scene_map_path, "Scene Map", scene.model_dump(mode="json"))

    def load_semantic(self) -> SceneMap:
        payload = read_markdown(self.scene_map_path)
        return SceneMap.model_validate(payload) if payload else SceneMap()

    def save_capability(self, snapshot: CapabilitySnapshot) -> None:
        write_markdown(self.project_info_path, "Project Info", snapshot.project.model_dump(mode="json"))
        write_markdown(self.robot_capability_path, "Robot Capability", snapshot.robot.model_dump(mode="json"))
        write_markdown(
            self.product_operations_path,
            "Product Operations",
            {"items": [item.model_dump(mode="json") for item in snapshot.operations]},
        )
        write_markdown(
            self.behavior_norms_path,
            "Behavior Norms",
            {"items": [item.model_dump(mode="json") for item in snapshot.norms]},
        )
        write_markdown(
            self.operation_habits_path,
            "Operation Habits",
            {"items": [item.model_dump(mode="json") for item in snapshot.habits]},
        )

    def load_capability(self) -> CapabilitySnapshot:
        project_payload = read_markdown(self.project_info_path)
        robot_payload = read_markdown(self.robot_capability_path)
        operations = read_markdown(self.product_operations_path).get("items", [])
        norms = read_markdown(self.behavior_norms_path).get("items", [])
        habits = read_markdown(self.operation_habits_path).get("items", [])
        return CapabilitySnapshot(
            project=ProjectInfo.model_validate(project_payload) if project_payload else ProjectInfo(),
            robot=RobotCapability.model_validate(robot_payload) if robot_payload else RobotCapability(),
            operations=[ProductOperation.model_validate(item) for item in operations],
            norms=[BehaviorNorm.model_validate(item) for item in norms],
            habits=[OperationHabit.model_validate(item) for item in habits],
        )

    def save_system_state(
        self,
        events: list[SystemEvent],
        stats: list[ToolStats],
        availability: list[ToolAvailability],
    ) -> None:
        write_jsonl(self.event_history_path, [item.model_dump(mode="json") for item in events])
        write_json(self.tool_success_rate_path, [item.model_dump(mode="json") for item in stats])
        write_json(self.tool_availability_path, [item.model_dump(mode="json") for item in availability])

    def load_system_state(self) -> tuple[list[SystemEvent], list[ToolStats], list[ToolAvailability]]:
        events = [SystemEvent.model_validate(row) for row in read_jsonl(self.event_history_path)]
        stats = [ToolStats.model_validate(item) for item in read_json(self.tool_success_rate_path, [])]
        availability = [ToolAvailability.model_validate(item) for item in read_json(self.tool_availability_path, [])]
        return events, stats, availability
