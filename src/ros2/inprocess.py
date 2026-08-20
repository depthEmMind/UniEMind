"""In-process ROS 2 transport used by tests and simulation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.bus import DataBus
from ros2.interfaces import MessageCallback, ROS2Transport


class InProcessROS2Transport(ROS2Transport):
    def __init__(self, bus: DataBus | None = None) -> None:
        self.bus = bus or DataBus()
        self.services: dict[str, Any] = {}
        self.actions: dict[str, Any] = {}
        self._topics: dict[str, list[Any]] = defaultdict(list)

    async def publish(self, topic: str, message: Any) -> None:
        self._topics[topic].append(message)
        await self.bus.publish(topic, message)

    async def subscribe(self, topic: str, callback: MessageCallback) -> None:
        await self.bus.subscribe(topic, callback)

    async def call_service(self, service: str, request: Any) -> Any:
        handler = self.services.get(service)
        if handler is None:
            raise KeyError(f"unknown service: {service}")
        if callable(handler):
            result = handler(request)
            if hasattr(result, "__await__"):
                return await result
            return result
        return handler

    async def send_action(self, action: str, goal: Any) -> Any:
        handler = self.actions.get(action)
        if handler is None:
            raise KeyError(f"unknown action: {action}")
        if callable(handler):
            result = handler(goal)
            if hasattr(result, "__await__"):
                return await result
            return result
        return handler
