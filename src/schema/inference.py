"""Model-agnostic inference protocol."""

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from schema.base import ErrorDetail, Status, UniEMindModel


class InferenceBackend(str, Enum):
    PYTORCH = "pytorch"
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    OPENVINO = "openvino"
    TENSORFLOW = "tensorflow"
    CUSTOM = "custom"


class InferenceRequest(UniEMindModel):
    request_id: UUID = Field(default_factory=uuid4)
    model_id: str
    backend: InferenceBackend = InferenceBackend.CUSTOM
    inputs: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=5.0, gt=0)


class InferenceResponse(UniEMindModel):
    request_id: UUID
    status: Status
    outputs: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = Field(default=None, ge=0)
    error: ErrorDetail | None = None
