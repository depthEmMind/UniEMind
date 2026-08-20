import asyncio
from uuid import uuid4

from safety import SafetyGuard, SafetyLimits
from schema import ActionRequest, ActionType


def test_safety_blocks_velocity_and_workspace() -> None:
    async def scenario() -> tuple[bool, bool]:
        guard = SafetyGuard(SafetyLimits(max_linear_velocity=0.5))
        fast = await guard.evaluate(
            ActionRequest(
                task_id=uuid4(),
                execution_id=uuid4(),
                action_type=ActionType.CONTROLLER,
                target="base",
                command={"velocity": 2.0},
            )
        )
        outside = await guard.evaluate(
            ActionRequest(
                task_id=uuid4(),
                execution_id=uuid4(),
                action_type=ActionType.CONTROLLER,
                target="arm",
                command={"position": [99.0, 0.0, 0.5]},
            )
        )
        return fast.allowed, outside.allowed

    assert asyncio.run(scenario()) == (False, False)
