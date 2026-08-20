"""Shared schema primitives and API envelope models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "v1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UniEMindModel(BaseModel):
    """Strict base class for all stable UniEMind protocols."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, use_enum_values=False)


class Status(str, Enum):
    UNKNOWN = "UNKNOWN"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class ErrorCode(str, Enum):
    SUCCESS = "SUCCESS"
    INVALID_INPUT = "INVALID_INPUT"
    TIMEOUT = "TIMEOUT"
    NOT_READY = "NOT_READY"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(UniEMindModel):
    code: ErrorCode
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class Header(UniEMindModel):
    timestamp: datetime = Field(default_factory=utc_now)
    frame_id: str = "world"
    source: str
    sequence: int = Field(default=0, ge=0)
    schema_version: str = SCHEMA_VERSION


PayloadT = TypeVar("PayloadT")


class APIEnvelope(UniEMindModel, Generic[PayloadT]):
    version: str = SCHEMA_VERSION
    timestamp: datetime = Field(default_factory=utc_now)
    request_id: UUID = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4)
    source: str
    payload: PayloadT | None = None
    status: Status = Status.SUCCESS
    error: ErrorDetail | None = None
