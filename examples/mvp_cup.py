"""Run the first complete UniEMind MVP loop without robot hardware."""

import asyncio

from simulation import run_cup_demo


async def main() -> None:
    task, world_model = await run_cup_demo()
    cup = await world_model.get_object("cup-1")
    print(f"task={task.status.value}")
    print(f"steps={[step.status.value for step in task.steps]}")
    print(f"cup_grasped={bool(cup and cup.attributes.get('grasped'))}")


if __name__ == "__main__":
    asyncio.run(main())
