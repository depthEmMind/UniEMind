"""Text, API, and simulated voice interaction."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from schema import (
    InteractionRequest,
    InteractionResponse,
    InteractionType,
    Task,
)

TaskFactory = Callable[[InteractionRequest], Awaitable[Task] | Task]
TaskRunner = Callable[[Task], Awaitable[Task]]


class ConversationManager:
    """Maps InteractionRequest to a Task without knowing robot hardware."""

    def __init__(self, factory: TaskFactory, runner: TaskRunner) -> None:
        self.factory = factory
        self.runner = runner
        self.history: list[InteractionRequest] = []

    async def handle(self, request: InteractionRequest) -> InteractionResponse:
        self.history.append(request)
        task = self.factory(request)
        if hasattr(task, "__await__"):
            task = await task  # type: ignore[misc]
        completed = await self.runner(task)
        return InteractionResponse(
            session_id=request.session_id,
            request_id=request.request_id,
            status=completed.status,
            content=completed.goal,
            metadata={"task_id": str(completed.task_id), "steps": len(completed.steps)},
        )


class EchoVoiceManager:
    async def transcribe(self, audio: bytes) -> str:
        return audio.decode("utf-8", errors="ignore") or "go to the lab bench"

    async def speak(self, text: str) -> bytes:
        return text.encode("utf-8")


class InProcessAPI:
    def __init__(self, conversation: ConversationManager) -> None:
        self.conversation = conversation

    async def post_interaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = InteractionRequest.model_validate(payload)
        if request.type not in {
            InteractionType.TEXT,
            InteractionType.API,
            InteractionType.VOICE,
            InteractionType.ROS2_REMOTE,
        }:
            request = request.model_copy(update={"type": InteractionType.API})
        response = await self.conversation.handle(request)
        return response.model_dump(mode="json")
