"""Stable plugin lifecycle contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import Field

from schema.base import UniEMindModel


class PluginType(str, Enum):
    SENSOR = "sensor"
    ALGORITHM = "algorithm"
    MODEL = "model"
    SKILL = "skill"
    TOOL = "tool"
    AGENT = "agent"
    MEMORY = "memory"
    ROBOT = "robot"
    SIMULATION = "simulation"


class PluginMetadata(UniEMindModel):
    name: str
    version: str
    plugin_type: PluginType
    api_version: str = "v1"
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)


class Plugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata: ...

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None: ...

    @abstractmethod
    async def shutdown(self) -> None: ...

    @abstractmethod
    async def health(self) -> dict[str, Any]: ...
