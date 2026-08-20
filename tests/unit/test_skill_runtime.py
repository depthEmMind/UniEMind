import asyncio
from uuid import uuid4

from memory import MemoryRouter
from schema import ErrorCode, SkillRequest
from skills import SkillContext, SkillRegistry, SkillRuntime
from world_model import WorldModel


def test_unknown_skill_returns_standard_error() -> None:
    runtime = SkillRuntime(SkillRegistry(), SkillContext(WorldModel(), MemoryRouter()))
    result = asyncio.run(
        runtime.execute(SkillRequest(task_id=uuid4(), skill_name="missing"))
    )
    assert result.error is not None
    assert result.error.code == ErrorCode.NOT_FOUND
