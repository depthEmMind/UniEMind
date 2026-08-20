import asyncio
from uuid import uuid4

from safety import SafetyGuard
from schema import ActionRequest, ActionType


def _request(**changes: object) -> ActionRequest:
    data = {
        "task_id": uuid4(),
        "execution_id": uuid4(),
        "action_type": ActionType.CONTROLLER,
        "target": "base",
        "command": {"velocity": 0.2},
    }
    data.update(changes)
    return ActionRequest.model_validate(data)


def test_safety_guard_blocks_bypass_and_emergency_stop() -> None:
    async def scenario() -> tuple[bool, bool]:
        guard = SafetyGuard()
        bypass = await guard.evaluate(_request(requires_safety_check=False))
        await guard.set_emergency_stop(True)
        stopped = await guard.evaluate(_request())
        return bypass.allowed, stopped.allowed

    assert asyncio.run(scenario()) == (False, False)
