import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from memory import MemoryConfig, MultiLayerMemorySystem
from schema.memory import (
    BehaviorNorm,
    EventTrajectory,
    OperationHabit,
    ProductOperation,
    ProjectInfo,
    RobotCapability,
    SceneObject,
)


def test_working_update_clear_and_capacity(tmp_path: Path) -> None:
    async def scenario() -> None:
        system = MultiLayerMemorySystem(tmp_path / "memory", MemoryConfig(working_limit=2))
        await system.update_working(session_id="s", task_id="t", user_request="start", result={"n": 1})
        await system.update_working(session_id="s", task_id="t", result={"n": 2})
        await system.update_working(session_id="s", task_id="t", result={"n": 3})
        node = await system.working.get("t")
        assert node is not None
        assert [item["n"] for item in node.intermediate_results] == [2, 3]
        assert await system.working.clear("t") == 1
        assert await system.working.get("t") is None

    asyncio.run(scenario())


def test_episodic_query_modify_forget_and_delete(tmp_path: Path) -> None:
    async def scenario() -> None:
        system = MultiLayerMemorySystem(tmp_path / "memory")
        first = datetime(2026, 8, 20, 1, tzinfo=timezone.utc)
        second = first + timedelta(hours=1)
        stored = await system.append_episode(
            EventTrajectory(event="find_cup", node="perception", description="saw cup", timestamp=first, confidence=0.2)
        )
        await system.append_episode(
            EventTrajectory(event="grasp", node="skill", description="failed grasp", timestamp=second, confidence=1.0)
        )
        assert await system.episodic.times_of("find_cup") == [first]
        await system.episodic.modify(stored.event_id, description="saw cup on bench")
        updated = await system.episodic.query(event="find_cup")
        assert updated[0].description == "saw cup on bench"
        assert await system.episodic.forget(now=first + timedelta(days=30), decay=0.01) == 1
        assert await system.episodic.delete_between(second - timedelta(minutes=1), second + timedelta(minutes=1)) == 1

    asyncio.run(scenario())


def test_semantic_location_relation_and_decay(tmp_path: Path) -> None:
    async def scenario() -> None:
        system = MultiLayerMemorySystem(
            tmp_path / "memory", MemoryConfig(object_unseen_seconds=10, confidence_forget_threshold=0.2)
        )
        await system.upsert_object(
            SceneObject(
                name="cup",
                location="lab_bench",
                description="white cup",
                relations={"on": "table", "beside": "sink"},
            )
        )
        await system.upsert_object(SceneObject(name="bottle", location="sink", relations={"in": "rack"}))
        local = await system.semantic.load_local(location="lab_bench")
        related = await system.semantic.query(relation=("on", "table"))
        assert local[0].name == "cup"
        assert len(related) == 1
        scene = await system.semantic.dump()
        scene.objects[0] = scene.objects[0].model_copy(
            update={"last_seen": datetime.now(timezone.utc) - timedelta(seconds=30), "confidence": 0.5}
        )
        await system.semantic.load(scene)
        assert await system.semantic.forget() >= 1
        remaining = await system.semantic.query(name="cup", present_only=False)
        assert remaining
        assert remaining[0].present is False
        assert await system.semantic.mark_absent("bottle") is True
        assert await system.semantic.clear() >= 1

    asyncio.run(scenario())


def test_capability_static_dynamic_and_habits(tmp_path: Path) -> None:
    async def scenario() -> None:
        system = MultiLayerMemorySystem(tmp_path / "memory", MemoryConfig(habit_confidence_threshold=0.3))
        await system.capability.set_project(ProjectInfo(name="UniEMind", tasks=["pick_cup"]))
        await system.capability.set_robot(RobotCapability(skills=["navigate_to", "grasp_object"]))
        await system.capability.upsert_operation(
            ProductOperation(product="cup", steps=["approach from the side", "grasp body"])
        )
        await system.capability.upsert_norm(BehaviorNorm(rule_id="n1", task_type="grasp", rule="stay below 0.2 m/s"))
        await system.capability.add_habit(OperationHabit(habit_id="h1", description="retry grasp once", confidence=0.1))
        await system.capability.add_habit(OperationHabit(habit_id="h2", description="align gripper", confidence=0.9))
        by_product = await system.capability.query(product="cup")
        assert by_product["operations"][0].product == "cup"
        skills = await system.capability.query(skills=True)
        assert skills["skills"] == ["navigate_to", "grasp_object"]
        assert await system.capability.forget() == 1
        updated = await system.capability.modify_operation("cup", parameters={"force": 12})
        assert updated.parameters["force"] == 12
        assert await system.capability.delete_operation("cup") is True
        assert await system.capability.clear_dynamic() >= 1
        snapshot = await system.capability.dump()
        assert snapshot.project.name == "UniEMind"
        assert snapshot.robot.skills == ["navigate_to", "grasp_object"]
        assert snapshot.operations == []

    asyncio.run(scenario())


def test_system_state_stats_window_and_unavailable(tmp_path: Path) -> None:
    async def scenario() -> None:
        system = MultiLayerMemorySystem(
            tmp_path / "memory",
            MemoryConfig(availability_rate_threshold=0.5, event_history_window_seconds=60),
        )
        await system.record_tool("grasp_object", True)
        await system.record_tool("grasp_object", False)
        await system.record_tool("grasp_object", False)
        queried = await system.system_state.query_tool("grasp_object")
        assert queried["stats"] is not None
        assert queried["stats"].success_rate < 0.5
        assert len(await system.system_state.unavailable_tools()) == 1
        await system.system_state.modify_stats("grasp_object", successes=9, failures=1)
        await system.system_state.set_available("grasp_object", True, "manual override")
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        events = await system.system_state.dump_events()
        await system.system_state.load(
            [events[0].model_copy(update={"timestamp": old}), *events[1:]],
            await system.system_state.dump_stats(),
            await system.system_state.dump_availability(),
        )
        assert await system.system_state.forget() == 1
        assert await system.system_state.clear(keep_stats=True) >= 1
        assert len(await system.system_state.dump_stats()) == 1
        assert await system.system_state.delete_tool("grasp_object") is True

    asyncio.run(scenario())


def test_consolidation_llm_then_raw_then_emergency(tmp_path: Path) -> None:
    async def scenario() -> None:
        config = MemoryConfig(token_limit=40, episodic_keep_recent=2)

        async def summarize(events: list[EventTrajectory]) -> str:
            return f"summary:{len(events)}"

        llm_system = MultiLayerMemorySystem(tmp_path / "llm", config, llm=summarize)
        for index in range(12):
            await llm_system.append_episode(
                EventTrajectory(event="trace", description="cup " * 20 + str(index), confidence=0.5)
            )
        llm_report = await llm_system.consolidate()
        assert llm_report.strategy == "llm"

        async def boom(_events: list[EventTrajectory]) -> str:
            raise RuntimeError("llm unavailable")

        raw_system = MultiLayerMemorySystem(tmp_path / "raw", config, llm=boom)
        for index in range(12):
            await raw_system.append_episode(
                EventTrajectory(event="trace", description="cup " * 20 + str(index), confidence=0.5)
            )
        raw_report = await raw_system.consolidate()
        assert raw_report.strategy == "raw_dump"

        emergency = MultiLayerMemorySystem(tmp_path / "emergency", config)

        def fail_archive(*_args: object, **_kwargs: object) -> Path:
            raise OSError("disk full")

        emergency.store.archive_events = fail_archive  # type: ignore[method-assign]
        for index in range(12):
            await emergency.append_episode(
                EventTrajectory(
                    event="trace",
                    description="cup " * 20 + str(index),
                    confidence=0.1 if index < 8 else 1.0,
                )
            )
        emergency_report = await emergency.consolidate()
        assert emergency_report.strategy in {"raw_dump", "emergency_discard"}

    asyncio.run(scenario())


def test_async_consolidation_does_not_block_working_updates(tmp_path: Path) -> None:
    async def scenario() -> None:
        config = MemoryConfig(token_limit=40, episodic_keep_recent=1)

        async def slow(events: list[EventTrajectory]) -> str:
            await asyncio.sleep(0.2)
            return f"slow:{len(events)}"

        system = MultiLayerMemorySystem(tmp_path / "memory", config, llm=slow)
        for index in range(8):
            await system.append_episode(EventTrajectory(event="trace", description="token " * 30 + str(index)))
        task = system.consolidate_later()
        node = await system.update_working(session_id="s", task_id="live", user_request="still interacting")
        report = await task
        assert node.user_request == "still interacting"
        assert report.strategy in {"llm", "raw_dump", "none"}

    asyncio.run(scenario())
