"""Runtime plugin registry."""

from __future__ import annotations

from typing import Any

from plugins.base import Plugin, PluginType


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"plugin already registered: {name}")
        self._plugins[name] = plugin

    def get(self, name: str) -> Plugin:
        return self._plugins[name]

    def by_type(self, plugin_type: PluginType) -> list[Plugin]:
        return [plugin for plugin in self._plugins.values() if plugin.metadata.plugin_type == plugin_type]

    async def initialize_all(self, config: dict[str, Any] | None = None) -> None:
        for plugin in self._plugins.values():
            await plugin.initialize(config or {})

    async def shutdown_all(self) -> None:
        for plugin in self._plugins.values():
            await plugin.shutdown()
