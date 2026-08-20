"""Memory subsystem configuration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MemoryConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    persistence: str = "files"
    root: str = "data/memory"
    working_limit: int = Field(default=128, gt=0)
    token_limit: int = Field(default=8000, gt=0)
    habit_confidence_threshold: float = Field(default=0.2, ge=0, le=1)
    object_unseen_seconds: float = Field(default=86400.0, gt=0)
    event_history_window_seconds: float = Field(default=604800.0, gt=0)
    availability_rate_threshold: float = Field(default=0.3, ge=0, le=1)
    episodic_keep_recent: int = Field(default=32, gt=0)
    confidence_forget_threshold: float = Field(default=0.15, ge=0, le=1)
    inject_limit: int = Field(default=5, gt=0, le=100)
