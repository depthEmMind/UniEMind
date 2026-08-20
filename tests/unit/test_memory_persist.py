import asyncio
from pathlib import Path

from memory import JsonMemoryArchive, MemoryKind, MemoryQuery, MemoryRecord, MemoryRouter


def test_persist_and_consolidate_working_memory(tmp_path: Path) -> None:
    async def scenario() -> tuple[int, int, int, int, int]:
        router = MemoryRouter()
        await router.remember(
            MemoryRecord(kind=MemoryKind.WORKING, content={"note": "saw a cup"}, tags={"cup"})
        )
        moved = await router.consolidate_working()
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
