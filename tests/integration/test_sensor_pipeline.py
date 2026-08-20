import asyncio

from uniemind.core import DataBus
from uniemind.schema import Header, SensorData, SensorDataType


def test_adapter_output_can_flow_over_data_bus() -> None:
    async def scenario() -> SensorData:
        bus = DataBus()
        future: asyncio.Future[SensorData] = asyncio.get_running_loop().create_future()

        async def perception_input(message: SensorData) -> None:
            future.set_result(message)

        await bus.subscribe("sensor/front", perception_input)
        source = SensorData(
            header=Header(source="adapter"),
            sensor_id="front",
            data_type=SensorDataType.IMAGE,
            payload={"encoding": "rgb8"},
        )
        await bus.publish("sensor/front", source)
        return await future

    assert asyncio.run(scenario()).sensor_id == "front"
