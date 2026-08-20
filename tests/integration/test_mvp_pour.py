import asyncio

from schema import Status, TaskStepStatus
from simulation import run_pour_demo


def test_second_closed_loop_pours_at_sink() -> None:
    task, world_model = asyncio.run(run_pour_demo())
    cup = asyncio.run(world_model.get_object("cup-1"))
    snapshot = asyncio.run(world_model.snapshot())

    assert task.status == Status.SUCCESS
    assert all(step.status == TaskStepStatus.COMPLETED for step in task.steps)
    assert cup is not None
    assert cup.attributes["poured"] is True
    assert snapshot.robot is not None
    assert snapshot.robot.pose.position.x == 2.5
