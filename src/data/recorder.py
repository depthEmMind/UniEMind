"""JSONL recorder and replay for UniEMindData messages."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from core.bus import DataBus
from schema import SensorData


class DataRecorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def append(self, data: SensorData) -> None:
        self._handle.write(data.model_dump_json() + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> DataRecorder:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class DataReplay:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def iter_messages(self) -> Iterable[SensorData]:
        with self.path.open(encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if line:
                    yield SensorData.model_validate_json(line)

    async def publish_to(self, bus: DataBus, topic: str) -> int:
        count = 0
        for message in self.iter_messages():
            await bus.publish(topic, message)
            count += 1
        return count
