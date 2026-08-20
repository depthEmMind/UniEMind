import asyncio
from pathlib import Path

from memory import MemoryConfig, MultiLayerMemorySystem
from schema.memory import EventTrajectory, ProductOperation, RobotCapability, SceneObject


def test_request_retrieves_four_long_term_layers_then_writes_working(tmp_path: Path) -> None:
    async def scenario() -> None:
        system = MultiLayerMemorySystem(tmp_path / "memory", MemoryConfig(availability_rate_threshold=0.8))
        await system.append_episode(
            EventTrajectory(event="find_cup", node="perception", description="昨天在实验台看到杯子")
        )
        await system.upsert_object(
            SceneObject(name="cup", location="lab_bench", description="杯子通常放在实验台")
        )
        await system.capability.set_robot(RobotCapability(skills=["grasp_object"]))
        await system.capability.upsert_operation(
            ProductOperation(product="cup", steps=["从侧面接近杯子", "grasp the body"])
        )
        await system.record_tool("grasp_object", False)
        await system.record_tool("grasp_object", False)
        context = await system.handle_request(
            "去实验台拿一个杯子",
            session_id="demo",
            task_id="cup-1",
            pending_steps=[{"skill": "find_object"}],
        )
        working = await system.working.get("cup-1")
        assert working is not None
        assert "杯子" in working.user_request
        assert any("find_cup" in str(item.content) or "杯子" in str(item.content) for item in context.episodic)
        assert any(item.content.get("name") == "cup" for item in context.semantic)
        assert any(
            "cup" in str(item.content).casefold() or "grasp" in str(item.content).casefold()
            for item in context.capability
        )
        assert any(
            item.content.get("available") is False or item.content.get("name") == "grasp_object"
            for item in context.system_state
        )
        await system.update_working(session_id="demo", task_id="cup-1", result={"found": "cup"})
        await system.finish_task("cup-1", summary="杯子在实验台上")
        assert await system.working.get("cup-1") is None
        latest = await system.episodic.latest_scene()
        assert "杯子" in latest.text

    asyncio.run(scenario())
