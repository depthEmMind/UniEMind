import asyncio

from uniemind.core import DataBus


def test_data_bus_delivers_to_topic_and_wildcard() -> None:
    async def scenario() -> list[int]:
        bus = DataBus()
        received: list[int] = []

        async def subscriber(message: int) -> None:
            received.append(message)

        await bus.subscribe("sensor/image", subscriber)
        await bus.subscribe("*", subscriber)
        await bus.publish("sensor/image", 7)
        return received

    assert asyncio.run(scenario()) == [7, 7]
