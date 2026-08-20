"""Demonstrate config loading and standard robot-state publication."""

import asyncio
from pathlib import Path

from uniemind.config import load_config
from uniemind.core import DataBus
from uniemind.schema import Header, RobotProfile, RobotState, Status


async def main() -> None:
    root = Path(__file__).parents[1]
    profile = load_config(root / "configs/robot/demo_robot.yaml", RobotProfile)
    bus = DataBus()

    async def observe(state: RobotState) -> None:
        print(f"{profile.name}: {state.controller_state.value}")

    await bus.subscribe("robot/state", observe)
    await bus.publish(
        "robot/state",
        RobotState(
            header=Header(source=profile.name, frame_id=profile.frame_id),
            controller_state=Status.READY,
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
