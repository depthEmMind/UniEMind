import asyncio

from memory import MemoryKind, MemoryQuery, MemoryRecord, MemoryRouter


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
        return await router.retrieve(
            MemoryQuery(text="cup", kinds={MemoryKind.CAPABILITY}, tags={"cup"})
        )

    records = asyncio.run(scenario())
    assert len(records) == 1
    assert records[0].kind == MemoryKind.CAPABILITY
