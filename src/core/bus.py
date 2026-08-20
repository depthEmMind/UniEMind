"""In-process asynchronous data bus with explicit topic boundaries."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

Subscriber = Callable[[Any], Awaitable[None]]


class DataBus:
    """Small runtime bus suitable for tests and single-process deployments."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        async with self._lock:
            if subscriber not in self._subscribers[topic]:
                self._subscribers[topic].append(subscriber)

    async def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        async with self._lock:
            if subscriber in self._subscribers.get(topic, []):
                self._subscribers[topic].remove(subscriber)

    async def publish(self, topic: str, message: Any) -> None:
        async with self._lock:
            subscribers = [*self._subscribers.get(topic, []), *self._subscribers.get("*", [])]
        if subscribers:
            await asyncio.gather(*(subscriber(message) for subscriber in subscribers))
