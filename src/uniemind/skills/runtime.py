"""Skill lifecycle, registry, and observable execution runtime."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from uniemind.memory import MemoryRouter
from uniemind.schema import ErrorCode, ErrorDetail, SkillMetadata, SkillRequest, SkillResult, Status
from uniemind.world_model import WorldModel


class SkillContext:
    def __init__(self, world_model: WorldModel, memory: MemoryRouter) -> None:
        self.world_model = world_model
        self.memory = memory


class Skill(ABC):
    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata: ...

    @abstractmethod
    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult: ...

    async def cancel(self, execution_id: str) -> None:
        return None

    async def monitor(self, execution_id: str) -> Status:
        return Status.UNKNOWN

    async def recover(
        self, request: SkillRequest, result: SkillResult, context: SkillContext
    ) -> SkillResult:
        return result


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        name = skill.metadata.name
        if name in self._skills:
            raise ValueError(f"skill already registered: {name}")
        self._skills[name] = skill

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"unknown skill: {name}") from exc

    def metadata(self) -> list[SkillMetadata]:
        return [skill.metadata for skill in self._skills.values()]


class SkillRuntime:
    def __init__(self, registry: SkillRegistry, context: SkillContext) -> None:
        self.registry = registry
        self.context = context

    async def execute(self, request: SkillRequest) -> SkillResult:
        try:
            skill = self.registry.get(request.skill_name)
        except KeyError as exc:
            return self._failure(request, ErrorCode.NOT_FOUND, str(exc))
        try:
            if request.timeout_seconds is None:
                return await skill.execute(request, self.context)
            return await asyncio.wait_for(
                skill.execute(request, self.context), timeout=request.timeout_seconds
            )
        except asyncio.TimeoutError:
            await skill.cancel(str(request.execution_id))
            return self._failure(request, ErrorCode.TIMEOUT, "skill timed out")
        except Exception as exc:
            return self._failure(request, ErrorCode.EXECUTION_FAILED, str(exc))

    @staticmethod
    def _failure(request: SkillRequest, code: ErrorCode, message: str) -> SkillResult:
        return SkillResult(
            execution_id=request.execution_id,
            status=Status.FAILED,
            error=ErrorDetail(code=code, message=message),
        )
