"""Deterministic detector used when no vendor model is loaded."""

from __future__ import annotations

from perception.base import PerceptionAlgorithm
from schema import Header, Observation, ObservedObject, SensorData
from schema.base import Status
from schema.geometry import Pose, Vector3
from schema.inference import InferenceRequest, InferenceResponse


class MockObjectDetector(PerceptionAlgorithm):
    name = "mock_object_detector"

    def __init__(self, objects: list[ObservedObject] | None = None) -> None:
        self.objects = objects or [
            ObservedObject(
                object_id="cup-1",
                label="cup",
                confidence=0.96,
                pose=Pose(position=Vector3(x=1.2, y=0.4, z=0.8), frame_id="map"),
                attributes={"support_surface": "table"},
            )
        ]

    async def infer(self, sensor: SensorData) -> Observation:
        return Observation(
            header=Header(
                source=self.name,
                frame_id=sensor.header.frame_id,
                sequence=sensor.header.sequence,
            ),
            observer=sensor.sensor_id,
            objects=[item.model_copy(deep=True) for item in self.objects],
        )

    async def inference_roundtrip(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            request_id=request.request_id,
            status=Status.SUCCESS,
            outputs={"objects": [item.model_dump(mode="json") for item in self.objects]},
            latency_ms=1.0,
        )
