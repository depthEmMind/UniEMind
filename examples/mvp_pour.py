"""Run the second specification closed loop in simulation."""

import asyncio

from simulation import run_pour_demo


async def main() -> None:
    task, world_model = await run_pour_demo()
    cup = await world_model.get_object("cup-1")
    robot = (await world_model.snapshot()).robot
    print(f"task={task.status.value}")
    print(f"steps={[step.status.value for step in task.steps]}")
    print(f"cup_poured={bool(cup and cup.attributes.get('poured'))}")
    print(f"robot_pose={robot.pose.position.x if robot else None}")


if __name__ == "__main__":
    asyncio.run(main())
