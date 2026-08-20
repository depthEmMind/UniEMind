"""Independent safety authorization boundary for every action."""

from __future__ import annotations

import asyncio

from pydantic import Field

from uniemind.schema import ActionRequest
from uniemind.schema.base import UniEMindModel


class SafetyDecision(UniEMindModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)


class SafetyGuard:
    def __init__(self, *, max_action_timeout: float = 120.0) -> None:
        self.max_action_timeout = max_action_timeout
        self._emergency_stop = False
        self._lock = asyncio.Lock()

    async def set_emergency_stop(self, active: bool) -> None:
        async with self._lock:
            self._emergency_stop = active

    async def evaluate(self, request: ActionRequest) -> SafetyDecision:
        async with self._lock:
            emergency_stop = self._emergency_stop
        reasons: list[str] = []
        if emergency_stop:
            reasons.append("emergency stop is active")
        if not request.requires_safety_check:
            reasons.append("actions may not bypass safety checks")
        if request.timeout_seconds > self.max_action_timeout:
            reasons.append("action timeout exceeds configured safety limit")
        if not request.target.strip():
            reasons.append("action target is empty")
        return SafetyDecision(allowed=not reasons, reasons=reasons)
