"""JSON persistence for memory records."""

from __future__ import annotations

import json
from pathlib import Path

from memory.core import MemoryRecord, MemoryRouter


class JsonMemoryArchive:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    async def save(self, router: MemoryRouter) -> int:
        records = await router.dump()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.model_dump(mode="json") for record in records]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return len(payload)

    async def load(self, router: MemoryRouter) -> int:
        if not self.path.exists():
            return 0
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        count = 0
        for item in payload:
            await router.remember(MemoryRecord.model_validate(item))
            count += 1
        return count
