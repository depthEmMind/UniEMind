import asyncio
from pathlib import Path

from core import DataBus
from data import DataRecorder, DataReplay, DictImageAdapter
from schema import SensorDataType


def test_record_and_replay_round_trip(tmp_path: Path) -> None:
    adapter = DictImageAdapter()
    sensor = adapter.adapt({"width": 8, "height": 8, "data": b"x" * 8, "sequence": 3})
    path = tmp_path / "bag.jsonl"

    async def scenario() -> int:
        with DataRecorder(path) as recorder:
            recorder.append(sensor)
        bus = DataBus()
        received: list[int] = []

        async def on_message(message) -> None:
            received.append(message.header.sequence)

        await bus.subscribe("replay", on_message)
        count = await DataReplay(path).publish_to(bus, "replay")
        assert received == [3]
        assert sensor.data_type == SensorDataType.IMAGE
        return count

    assert asyncio.run(scenario()) == 1
