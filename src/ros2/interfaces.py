"""ROS 2-facing abstractions that keep rclpy out of the cognitive core."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from schema.sensor import SensorData

RawT = TypeVar("RawT")
MessageCallback = Callable[[Any], Awaitable[None]]


class ROS2Transport(ABC):
    """Replaceable ROS 2 transport boundary."""

    @abstractmethod
    async def publish(self, topic: str, message: Any) -> None: ...

    @abstractmethod
    async def subscribe(self, topic: str, callback: MessageCallback) -> None: ...

    @abstractmethod
    async def call_service(self, service: str, request: Any) -> Any: ...

    @abstractmethod
    async def send_action(self, action: str, goal: Any) -> Any: ...


class SensorAdapter(ABC, Generic[RawT]):
    """Converts a vendor/ROS message into a standard UniEMind message."""

    @abstractmethod
    def adapt(self, message: RawT) -> SensorData: ...
