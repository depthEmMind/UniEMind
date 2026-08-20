import asyncio
from pathlib import Path

from config import load_config
from memory import LONG_TERM_KINDS, MemoryConfig, MemoryKind, MemoryQuery, MemoryRecord, MemoryRouter


def test_router_searches_selected_memory_layers() -> None:
    async def scenario() -> list[MemoryRecord]:
        router = MemoryRouter()
        await router.remember(
            MemoryRecord(
                kind=MemoryKind.CAPABILITY,
                content={"skill": "grasp", "hint": "approach cup from the side"},
                tags={"cup"},
            )
        )
        await router.remember(
            MemoryRecord(kind=MemoryKind.SEMANTIC, content={"fact": "cups hold liquid"})
        )
        return await router.query(
            MemoryQuery(text="cup", kinds={MemoryKind.CAPABILITY}, tags={"cup"})
        )

    records = asyncio.run(scenario())
    assert len(records) == 1
    assert records[0].kind == MemoryKind.CAPABILITY


def test_router_injects_long_term_layers_only() -> None:
    async def scenario() -> tuple[int, int, int, int]:
        router = MemoryRouter()
        await router.update(MemoryRecord(kind=MemoryKind.WORKING, content={"note": "scratch pad cup"}))
        await router.update(MemoryRecord(kind=MemoryKind.SEMANTIC, content={"object": "cup", "location": "lab_bench"}))
        await router.update(
            MemoryRecord(kind=MemoryKind.CAPABILITY, content={"skill": "grasp_object", "object": "cup"})
        )
        context = await router.inject("cup")
        return (
            len(context.semantic),
            len(context.capability),
            len(context.episodic),
            len(context.system_state),
        )

    semantic, capability, episodic, system_state = asyncio.run(scenario())
    assert semantic == 1
    assert capability == 1
    assert episodic == 0
    assert system_state == 0
    assert {
        MemoryKind.EPISODIC,
        MemoryKind.SEMANTIC,
        MemoryKind.CAPABILITY,
        MemoryKind.SYSTEM_STATE,
    } == LONG_TERM_KINDS


def test_memory_config_loads_from_yaml() -> None:
    config = load_config(Path("configs/memory/default.yaml"), MemoryConfig)
    assert config.persistence == "files"
    assert config.working_limit == 128
    assert config.token_limit == 8000
