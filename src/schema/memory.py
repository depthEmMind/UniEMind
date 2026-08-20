"""Schema-first protocols for the five-layer memory system."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from schema.base import UniEMindModel, utc_now


class TaskNode(UniEMindModel):
    session_id: str
    task_id: str
    user_request: str = ""
    pending_steps: list[dict[str, Any]] = Field(default_factory=list)
    intermediate_results: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "running"
    updated_at: datetime = Field(default_factory=utc_now)


class EventTrajectory(UniEMindModel):
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=utc_now)
    event: str
    node: str = ""
    scene_state: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    confidence: float = Field(default=1.0, ge=0, le=1)
    task_id: str | None = None


class SceneSummary(UniEMindModel):
    text: str = ""
    updated_at: datetime = Field(default_factory=utc_now)
    task_id: str | None = None


class SceneObject(UniEMindModel):
    name: str
    location: str = ""
    description: str = ""
    relations: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0, le=1)
    last_seen: datetime = Field(default_factory=utc_now)
    position: list[float] | None = None
    present: bool = True


class SceneMap(UniEMindModel):
    map_id: str = "default"
    notes: str = ""
    objects: list[SceneObject] = Field(default_factory=list)


class ProjectInfo(UniEMindModel):
    name: str = "UniEMind"
    version: str = "0.1.0"
    description: str = ""
    tasks: list[str] = Field(default_factory=list)


class RobotCapability(UniEMindModel):
    body: str = ""
    skills: list[str] = Field(default_factory=list)
    limits: dict[str, Any] = Field(default_factory=dict)


class ProductOperation(UniEMindModel):
    product: str
    steps: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class BehaviorNorm(UniEMindModel):
    rule_id: str
    task_type: str
    rule: str


class OperationHabit(UniEMindModel):
    habit_id: str
    description: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    source_task: str | None = None


class CapabilitySnapshot(UniEMindModel):
    project: ProjectInfo = Field(default_factory=ProjectInfo)
    robot: RobotCapability = Field(default_factory=RobotCapability)
    operations: list[ProductOperation] = Field(default_factory=list)
    norms: list[BehaviorNorm] = Field(default_factory=list)
    habits: list[OperationHabit] = Field(default_factory=list)


class SystemEvent(UniEMindModel):
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=utc_now)
    component: str
    name: str
    success: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class ToolStats(UniEMindModel):
    tool: str
    successes: int = Field(default=0, ge=0)
    failures: int = Field(default=0, ge=0)

    @property
    def attempts(self) -> int:
        return self.successes + self.failures

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 1.0
        return self.successes / self.attempts


class ToolAvailability(UniEMindModel):
    tool: str
    available: bool = True
    reason: str = ""


class MemorySnippet(UniEMindModel):
    kind: str
    content: dict[str, Any]
    relevance: float = Field(default=1.0, ge=0, le=1)
    tags: set[str] = Field(default_factory=set)


class MemoryContext(UniEMindModel):
    request: str
    episodic: list[MemorySnippet] = Field(default_factory=list)
    semantic: list[MemorySnippet] = Field(default_factory=list)
    capability: list[MemorySnippet] = Field(default_factory=list)
    system_state: list[MemorySnippet] = Field(default_factory=list)

    def as_prompt(self) -> str:
        sections = [f"User request: {self.request}"]
        for title, items in (
            ("Episodic", self.episodic),
            ("Semantic", self.semantic),
            ("Capability", self.capability),
            ("System state", self.system_state),
        ):
            if not items:
                continue
            body = "\n".join(f"- {item.content}" for item in items)
            sections.append(f"{title}:\n{body}")
        return "\n\n".join(sections)
