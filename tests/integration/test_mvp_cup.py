import asyncio

from uniemind.schema import Status, TaskStepStatus
from uniemind.simulation import run_cup_demo


def test_first_mvp_task_completes_closed_loop() -> None:
    task, world_model = asyncio.run(run_cup_demo())
    cup = asyncio.run(world_model.get_object("cup-1"))

    assert task.status == Status.SUCCESS
    assert all(step.status == TaskStepStatus.COMPLETED for step in task.steps)
    assert cup is not None
    assert cup.attributes["grasped"] is True
    assert asyncio.run(world_model.snapshot()).robot is not None
