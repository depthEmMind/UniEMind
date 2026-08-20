import asyncio

from ros2 import InProcessROS2Transport


def test_in_process_ros2_service_and_topic() -> None:
    async def scenario() -> tuple[str, str]:
        transport = InProcessROS2Transport()
        received: list[str] = []

        async def on_msg(message: str) -> None:
            received.append(message)

        await transport.subscribe("/chatter", on_msg)
        await transport.publish("/chatter", "ping")
        transport.services["/status"] = lambda request: "ok"
        reply = await transport.call_service("/status", {})
        return received[0], reply

    assert asyncio.run(scenario()) == ("ping", "ok")
