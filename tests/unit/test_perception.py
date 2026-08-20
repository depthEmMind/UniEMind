import asyncio

from perception import MockObjectDetector
from schema import Header, SensorData, SensorDataType
from world_model import WorldModel


def test_mock_detector_updates_world_model() -> None:
    async def scenario() -> str:
        detector = MockObjectDetector()
        world = WorldModel()
        observation = await detector.infer(
            SensorData(
                header=Header(source="camera", frame_id="map"),
                sensor_id="front",
                data_type=SensorDataType.IMAGE,
                payload={"width": 16, "height": 16},
            )
        )
        state = await world.apply_observation(observation)
        return next(iter(state.objects.values())).label

    assert asyncio.run(scenario()) == "cup"
