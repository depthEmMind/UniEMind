"""Concurrency-safe current-state world model."""

from __future__ import annotations

import asyncio

from uniemind.schema import Observation, ObservedObject, RobotState, WorldState
from uniemind.schema.base import utc_now


class WorldModel:
    """Maintains current belief state; it is intentionally not long-term memory."""

    def __init__(self, initial: WorldState | None = None) -> None:
        self._state = initial or WorldState()
        self._lock = asyncio.Lock()

    async def snapshot(self) -> WorldState:
        async with self._lock:
            return self._state.model_copy(deep=True)

    async def apply_observation(self, observation: Observation) -> WorldState:
        async with self._lock:
            for observed in observation.objects:
                self._state.objects[observed.object_id] = observed
            self._touch(observation.header.frame_id)
            return self._state.model_copy(deep=True)

    async def set_robot_state(self, robot: RobotState) -> WorldState:
        async with self._lock:
            self._state.robot = robot
            self._touch(self._state.frame_id)
            return self._state.model_copy(deep=True)

    async def upsert_object(self, observed: ObservedObject) -> WorldState:
        async with self._lock:
            self._state.objects[observed.object_id] = observed
            self._touch(self._state.frame_id)
            return self._state.model_copy(deep=True)

    async def get_object(self, object_id: str) -> ObservedObject | None:
        async with self._lock:
            observed = self._state.objects.get(object_id)
            return observed.model_copy(deep=True) if observed else None

    def _touch(self, frame_id: str) -> None:
        self._state.timestamp = utc_now()
        self._state.frame_id = frame_id
        self._state.revision += 1
