import asyncio
from uuid import uuid4

from monitoring import HealthMonitor
from observability import TraceContext
from schema import Status


def test_monitor_and_trace() -> None:
    async def scenario() -> Status:
        monitor = HealthMonitor()
        await monitor.report("robot", Status.READY)
        await monitor.report("agent", Status.RUNNING)
        monitor.register_watchdog("controller", lambda: Status.READY)
        await monitor.tick_watchdogs()
        return await monitor.overall()

    status = asyncio.run(scenario())
    assert status == Status.RUNNING
    trace = TraceContext.start(uuid4(), session_id="s1")
    child = trace.child()
    assert child.task_id == trace.task_id
    assert child.span_id != trace.span_id
