"""Sensor -> Adapter -> DataBus -> Perception -> World Model."""

import asyncio

from core import DataBus
from data import DictImageAdapter
from perception import MockObjectDetector
from world_model import WorldModel


async def main() -> None:
    bus = DataBus()
    world = WorldModel()
    detector = MockObjectDetector()
    adapter = DictImageAdapter()

    async def on_image(message) -> None:
        observation = await detector.infer(message)
        await world.apply_observation(observation)

    await bus.subscribe("sensor/front", on_image)
    await bus.publish(
        "sensor/front",
        adapter.adapt({"width": 640, "height": 480, "source": "front_camera", "sensor_id": "front"}),
    )
    state = await world.snapshot()
    print(f"objects={list(state.objects)}")


if __name__ == "__main__":
    asyncio.run(main())
