import asyncio
from typing import Any

from plugins import Plugin, PluginMetadata, PluginRegistry, PluginType
from schema import Status
from tools import calibrate_hand_eye, validate_tf


class DummySensorPlugin(Plugin):
    def __init__(self) -> None:
        self.ready = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_camera", version="v1", plugin_type=PluginType.SENSOR)

    async def initialize(self, config: dict[str, Any]) -> None:
        self.ready = True

    async def shutdown(self) -> None:
        self.ready = False

    async def health(self) -> dict[str, Any]:
        return {"ready": self.ready}


def test_plugin_registry_lifecycle() -> None:
    async def scenario() -> bool:
        registry = PluginRegistry()
        plugin = DummySensorPlugin()
        registry.register(plugin)
        await registry.initialize_all({})
        health = await plugin.health()
        await registry.shutdown_all()
        return health["ready"] is True and plugin.ready is False

    assert asyncio.run(scenario()) is True


def test_calibration_tools_succeed() -> None:
    hand_eye = calibrate_hand_eye()
    tf = validate_tf("base_link", "camera_link")
    assert hand_eye.status == Status.SUCCESS
    assert tf.details["connected"] is True
