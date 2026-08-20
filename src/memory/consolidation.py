"""Token-aware consolidation with LLM, raw-dump, and emergency fallbacks."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Protocol

from schema.base import UniEMindModel
from schema.memory import EventTrajectory

if TYPE_CHECKING:
    from memory.system import MultiLayerMemorySystem


LLMSummarizer = Callable[[list[EventTrajectory]], Awaitable[str]]


class TokenEstimate(UniEMindModel):
    system_tokens: int
    dialogue_tokens: int

    @property
    def total(self) -> int:
        return self.system_tokens + self.dialogue_tokens


class ConsolidationReport(UniEMindModel):
    strategy: str
    tokens_before: int
    tokens_after: int
    archived: int = 0
    discarded: int = 0
    summary: str = ""
    error: str = ""


class TokenEstimator:
    def estimate_text(self, text: str) -> int:
        cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        other = max(len(text) - cjk, 0)
        return cjk + (other + 3) // 4

    def estimate_payload(self, payload: object) -> int:
        return self.estimate_text(str(payload))

    async def estimate_system(self, system: MultiLayerMemorySystem) -> TokenEstimate:
        working = await system.working.list_tasks()
        events = await system.episodic.dump()
        summary = await system.episodic.latest_scene()
        scene = await system.semantic.dump()
        capability = await system.capability.dump()
        stats = await system.system_state.dump_stats()
        availability = await system.system_state.dump_availability()
        history = await system.system_state.dump_events()
        dialogue = self.estimate_payload((working, events, summary))
        system_tokens = self.estimate_payload((scene, capability, stats, availability, history))
        return TokenEstimate(system_tokens=system_tokens, dialogue_tokens=dialogue)


class EpisodicConsolidator(Protocol):
    async def compress(self, system: MultiLayerMemorySystem, estimate: TokenEstimate) -> ConsolidationReport: ...


class LLMEpisodicConsolidator:
    def __init__(self, summarizer: LLMSummarizer, keep_recent: int) -> None:
        self.summarizer = summarizer
        self.keep_recent = keep_recent

    async def compress(self, system: MultiLayerMemorySystem, estimate: TokenEstimate) -> ConsolidationReport:
        events = await system.episodic.dump()
        summary = await self.summarizer(events)
        archived = await system.episodic.keep_recent(self.keep_recent)
        await system.episodic.set_summary(summary)
        if archived:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            system.store.archive_events(stamp, archived)
        after = await TokenEstimator().estimate_system(system)
        await system.persist()
        return ConsolidationReport(
            strategy="llm",
            tokens_before=estimate.total,
            tokens_after=after.total,
            archived=len(archived),
            summary=summary,
        )


class RawDumpConsolidator:
    def __init__(self, keep_recent: int) -> None:
        self.keep_recent = keep_recent

    async def compress(self, system: MultiLayerMemorySystem, estimate: TokenEstimate) -> ConsolidationReport:
        events = await system.episodic.dump()
        archived = await system.episodic.keep_recent(self.keep_recent)
        kept = await system.episodic.dump()
        summary = " | ".join(item.description or item.event for item in kept[-8:])
        await system.episodic.set_summary(summary or "raw dump")
        if archived:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            system.store.archive_events(f"raw-{stamp}", archived)
        after = await TokenEstimator().estimate_system(system)
        await system.persist()
        return ConsolidationReport(
            strategy="raw_dump",
            tokens_before=estimate.total,
            tokens_after=after.total,
            archived=len(archived) or len(events) - len(kept),
            summary=summary,
        )


class EmergencyDiscardConsolidator:
    async def compress(self, system: MultiLayerMemorySystem, estimate: TokenEstimate) -> ConsolidationReport:
        discarded = 0
        estimator = TokenEstimator()
        after = await estimator.estimate_system(system)
        while after.total > max(system.config.token_limit // 2, 1):
            dropped = await system.episodic.drop_weakest(1)
            if dropped == 0:
                await system.working.clear()
                discarded += 1
                break
            discarded += dropped
            after = await estimator.estimate_system(system)
        await system.episodic.set_summary("emergency discard")
        await system.persist()
        return ConsolidationReport(
            strategy="emergency_discard",
            tokens_before=estimate.total,
            tokens_after=after.total,
            discarded=discarded,
            summary="emergency discard",
        )


class SystemStateUpdater:
    async def flush(self, system: MultiLayerMemorySystem) -> None:
        await system.persist_system_state()


class ConsolidationEngine:
    def __init__(
        self,
        *,
        estimator: TokenEstimator | None = None,
        llm: LLMSummarizer | None = None,
        keep_recent: int = 32,
    ) -> None:
        self.estimator = estimator or TokenEstimator()
        self.llm = llm
        self.keep_recent = keep_recent
        self.system_state_updater = SystemStateUpdater()

    async def maybe_consolidate(self, system: MultiLayerMemorySystem) -> ConsolidationReport:
        estimate = await self.estimator.estimate_system(system)
        if estimate.total <= system.config.token_limit:
            await self.system_state_updater.flush(system)
            return ConsolidationReport(strategy="none", tokens_before=estimate.total, tokens_after=estimate.total)
        report = await self._run_fallback_chain(system, estimate)
        await self.system_state_updater.flush(system)
        return report

    async def _run_fallback_chain(self, system: MultiLayerMemorySystem, estimate: TokenEstimate) -> ConsolidationReport:
        errors: list[str] = []
        if self.llm is not None:
            try:
                return await LLMEpisodicConsolidator(self.llm, self.keep_recent).compress(system, estimate)
            except Exception as exc:
                errors.append(f"llm:{exc}")
        try:
            return await RawDumpConsolidator(self.keep_recent).compress(system, estimate)
        except Exception as exc:
            errors.append(f"raw_dump:{exc}")
            report = await EmergencyDiscardConsolidator().compress(system, estimate)
            return report.model_copy(update={"error": "; ".join(errors)})
