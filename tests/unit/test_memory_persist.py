import asyncio
from pathlib import Path

from memory import JsonMemoryArchive, MemoryKind, MemoryQuery, MemoryRecord, MemoryRouter, MultiLayerMemorySystem
from schema.memory import EventTrajectory, SceneObject, TaskNode


def test_persist_and_consolidate_working_memory(tmp_path: Path) -> None:
    async def scenario() -> tuple[int, int, int, int, int]:
        router = MemoryRouter()
        await router.remember(
            MemoryRecord(kind=MemoryKind.WORKING, content={"note": "saw a cup"}, tags={"cup"})
        )
        moved = await router.consolidate()
        working = await router.retrieve(MemoryQuery(kinds={MemoryKind.WORKING}, text="cup"))
        episodic = await router.retrieve(MemoryQuery(kinds={MemoryKind.EPISODIC}, text="cup"))
        archive = JsonMemoryArchive(tmp_path / "memory.json")
        saved = await archive.save(router)
        restored = MemoryRouter()
        loaded = await archive.load(restored)
        return moved, len(working), len(episodic), saved, loaded

    moved, working, episodic, saved, loaded = asyncio.run(scenario())
    assert moved == 1
    assert working == 0
    assert episodic == 1
    assert saved == loaded == 1


def test_layered_file_store_round_trip(tmp_path: Path) -> None:
    async def scenario() -> tuple[bool, bool, str, str, int, str]:
        system = MultiLayerMemorySystem(tmp_path / "memory")
        await system.update_working(session_id="s1", task_id="t1", user_request="find cup")
        await system.append_episode(EventTrajectory(event="saw_cup", node="perception", description="cup on bench"))
        await system.upsert_object(SceneObject(name="cup", location="lab_bench", relations={"on": "table"}))
        await system.record_tool("grasp_object", True)
        await system.persist()
        restored = MultiLayerMemorySystem(tmp_path / "memory")
        await restored.load()
        working = await restored.working.get("t1")
        events = await restored.episodic.dump()
        objects = await restored.semantic.query(name="cup")
        stats = await restored.system_state.query_tool("grasp_object")
        return (
            (tmp_path / "memory" / "episodic" / "event_trajectory.jsonl").exists(),
            (tmp_path / "memory" / "semantic" / "scene_map.md").exists(),
            working.user_request if working else "",
            objects[0].location if objects else "",
            stats["stats"].successes if stats["stats"] else 0,
            events[0].event,
        )

    exists_events, exists_map, request, location, successes, event = asyncio.run(scenario())
    assert exists_events is True
    assert exists_map is True
    assert request == "find cup"
    assert location == "lab_bench"
    assert successes == 1
    assert event == "saw_cup"


def test_working_memory_reload_unfinished_task(tmp_path: Path) -> None:
    async def scenario() -> TaskNode | None:
        system = MultiLayerMemorySystem(tmp_path / "memory")
        await system.handle_request("pick up the cup", session_id="lab", task_id="task-9")
        restored = MultiLayerMemorySystem(tmp_path / "memory")
        await restored.load()
        return await restored.working.get("task-9")

    node = asyncio.run(scenario())
    assert node is not None
    assert node.user_request == "pick up the cup"
    assert node.session_id == "lab"
