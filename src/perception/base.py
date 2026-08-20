"""Algorithm-agnostic perception contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from schema import Observation, SensorData
from schema.inference import InferenceRequest, InferenceResponse


class PerceptionAlgorithm(ABC):
    """Converts standard sensor data into World Observations."""

    name: str

    @abstractmethod
    async def infer(self, sensor: SensorData) -> Observation: ...

    async def inference_roundtrip(self, request: InferenceRequest) -> InferenceResponse:
        raise NotImplementedError
