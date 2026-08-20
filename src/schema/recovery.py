"""Unified recovery policy used by skills, safety, and the agent."""

from enum import Enum

from pydantic import Field

from schema.base import UniEMindModel


class RecoveryAction(str, Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    RECOVER = "recover"
    REPLAN = "replan"
    DEGRADE = "degrade"
    ABORT = "abort"
    EMERGENCY_STOP = "emergency_stop"


class RecoveryPolicy(UniEMindModel):
    max_retries: int = Field(default=1, ge=0, le=10)
    fallback_skill: str | None = None
    on_exhausted: RecoveryAction = RecoveryAction.REPLAN
