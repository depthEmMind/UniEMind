"""Independent safety authorization boundary for every action."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import Field

from schema import ActionRequest
from schema.base import UniEMindModel


class SafetyDecision(UniEMindModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)


class SafetyLimits(UniEMindModel):
    max_action_timeout: float = Field(default=120.0, gt=0)
    max_linear_velocity: float = Field(default=1.5, gt=0)
    max_angular_velocity: float = Field(default=2.0, gt=0)
    workspace_min: tuple[float, float, float] = (-10.0, -10.0, 0.0)
    workspace_max: tuple[float, float, float] = (10.0, 10.0, 3.0)
    min_battery_percent: float = Field(default=5.0, ge=0, le=100)
    joint_min: float = -3.2
    joint_max: float = 3.2


class SafetyGuard:
    def __init__(self, limits: SafetyLimits | None = None) -> None:
        self.limits = limits or SafetyLimits()
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
        if request.timeout_seconds > self.limits.max_action_timeout:
            reasons.append("action timeout exceeds configured safety limit")
        if not request.target.strip():
            reasons.append("action target is empty")
        reasons.extend(self._command_violations(request.command))
        return SafetyDecision(allowed=not reasons, reasons=reasons)

    def _command_violations(self, command: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        velocity = command.get("velocity")
        if isinstance(velocity, (int, float)) and abs(velocity) > self.limits.max_linear_velocity:
            reasons.append("linear velocity exceeds limit")
        angular = command.get("angular_velocity")
        if isinstance(angular, (int, float)) and abs(angular) > self.limits.max_angular_velocity:
            reasons.append("angular velocity exceeds limit")
        battery = command.get("battery_percent")
        if isinstance(battery, (int, float)) and battery < self.limits.min_battery_percent:
            reasons.append("battery below safety threshold")
        pose = command.get("position")
        if isinstance(pose, (list, tuple)) and len(pose) == 3:
            for value, low, high in zip(
                pose, self.limits.workspace_min, self.limits.workspace_max, strict=True
            ):
                if not (low <= float(value) <= high):
                    reasons.append("commanded pose is outside workspace")
                    break
        joints = command.get("joints")
        if isinstance(joints, list):
            for value in joints:
                if not (self.limits.joint_min <= float(value) <= self.limits.joint_max):
                    reasons.append("joint command exceeds joint limit")
                    break
        if command.get("collision"):
            reasons.append("collision check failed")
        return reasons
