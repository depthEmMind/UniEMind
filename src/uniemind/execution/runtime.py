"""Safety-gated controller execution runtime."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from uniemind.safety import SafetyGuard
from uniemind.schema import ActionRequest, ActionResult, ErrorCode, ErrorDetail, Status


class Controller(ABC):
    @abstractmethod
    async def execute(self, request: ActionRequest) -> ActionResult: ...

    @abstractmethod
    async def cancel(self, action_id: str) -> None: ...


class ActionExecutor:
    def __init__(self, guard: SafetyGuard, controller: Controller) -> None:
        self.guard = guard
        self.controller = controller

    async def execute(self, request: ActionRequest) -> ActionResult:
        decision = await self.guard.evaluate(request)
        if not decision.allowed:
            return ActionResult(
                action_id=request.action_id,
                status=Status.FAILED,
                error=ErrorDetail(
                    code=ErrorCode.SAFETY_BLOCKED,
                    message="; ".join(decision.reasons),
                ),
            )
        try:
            return await asyncio.wait_for(
                self.controller.execute(request), timeout=request.timeout_seconds
            )
        except asyncio.TimeoutError:
            await self.controller.cancel(str(request.action_id))
            return ActionResult(
                action_id=request.action_id,
                status=Status.TIMEOUT,
                error=ErrorDetail(code=ErrorCode.TIMEOUT, message="controller action timed out"),
            )
        except Exception as exc:
            return ActionResult(
                action_id=request.action_id,
                status=Status.FAILED,
                error=ErrorDetail(code=ErrorCode.EXECUTION_FAILED, message=str(exc)),
            )
