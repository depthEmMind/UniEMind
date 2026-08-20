import asyncio

from schema import Header, Observation, ObservedObject
from world_model import WorldModel


def test_observation_updates_world_revision() -> None:
    async def scenario() -> tuple[int, str]:
        model = WorldModel()
        observation = Observation(
            header=Header(source="detector", frame_id="map"),
            observer="front_camera",
            objects=[ObservedObject(object_id="cup-1", label="cup", confidence=0.9)],
        )
        state = await model.apply_observation(observation)
        return state.revision, state.objects["cup-1"].label

    assert asyncio.run(scenario()) == (1, "cup")
