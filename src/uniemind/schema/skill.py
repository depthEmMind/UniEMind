"""Stable skill contract schemas."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from uniemind.schema.base import ErrorDetail, Status, UniEMindModel


class SkillMetadata(UniEMindModel):
    name: str
    version: str
    category: str
    description: str = ""
    required_capabilities: set[str] = Field(default_factory=set)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)


class SkillRequest(UniEMindModel):
    execution_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    skill_name: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float | None = Field(default=None, gt=0)


class SkillResult(UniEMindModel):
    execution_id: UUID
    status: Status
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: ErrorDetail | None = None
