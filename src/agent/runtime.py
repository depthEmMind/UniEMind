"""Framework-neutral planning, graphs, ReAct, and recovery harness."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from schema import RecoveryPolicy, SkillRequest, Status, Task, TaskStep, TaskStepStatus
from skills import SkillRuntime


class Planner(ABC):
    @abstractmethod
    async def plan(self, task: Task) -> Task: ...

    async def replan(self, task: Task, failed_step: int) -> Task:
        remaining = [
            step.model_copy(update={"status": TaskStepStatus.PENDING, "error": None})
            for step in task.steps[failed_step:]
        ]
        return task.model_copy(update={"steps": task.steps[:failed_step] + remaining})


class StaticPlanner(Planner):
    async def plan(self, task: Task) -> Task:
        if not task.steps:
            raise ValueError("static planner requires pre-populated task steps")
        return task


class GoalPlanner(Planner):
    """Keyword planner covering the two specification closed-loop tasks."""

    async def plan(self, task: Task) -> Task:
        if task.steps:
            return task
        goal = task.goal.casefold()
        if "pour" in goal or "倒" in goal:
            steps = [
                TaskStep(name="navigate to lab bench", skill="navigate_to", inputs={"location": "lab_bench"}),
                TaskStep(name="find cup", skill="find_object", inputs={"label": "cup"}),
                TaskStep(name="grasp cup", skill="grasp_object", inputs={"object_id": "$last.object_id"}),
                TaskStep(name="navigate to sink", skill="navigate_to", inputs={"location": "sink"}),
                TaskStep(name="pour", skill="pour", inputs={"object_id": "$last.object_id"}),
                TaskStep(name="verify pour", skill="verify_pour", inputs={"object_id": "$last.object_id"}),
            ]
        else:
            steps = [
                TaskStep(name="find cup", skill="find_object", inputs={"label": "cup"}),
                TaskStep(name="approach", skill="navigate_to_object", inputs={"object_id": "$last.object_id"}),
                TaskStep(name="grasp", skill="grasp_object", inputs={"object_id": "$last.object_id"}),
                TaskStep(name="verify grasp", skill="verify_grasp", inputs={"object_id": "$last.object_id"}),
            ]
        return task.model_copy(update={"steps": steps})


def bind_inputs(inputs: dict[str, Any], last_outputs: dict[str, Any]) -> dict[str, Any]:
    bound: dict[str, Any] = {}
    for key, value in inputs.items():
        if isinstance(value, str) and value.startswith("$last."):
            bound[key] = last_outputs.get(value.removeprefix("$last."))
        else:
            bound[key] = value
    return bound


class AgentHarness:
    """Runs Plan -> Skill -> Monitor/Evaluate with retry and replan."""

    def __init__(
        self,
        planner: Planner,
        skills: SkillRuntime,
        policy: RecoveryPolicy | None = None,
    ) -> None:
        self.planner = planner
        self.skills = skills
        self.policy = policy or RecoveryPolicy()

    async def run(self, task: Task) -> Task:
        task = await self.planner.plan(task)
        task.status = Status.RUNNING
        last_outputs: dict[str, Any] = {}
        index = 0
        while index < len(task.steps):
            step = task.steps[index]
            task.current_step = index
            step.status = TaskStepStatus.RUNNING
            if not step.skill:
                step.status = TaskStepStatus.FAILED
                step.error = "task step has no skill"
                task.status = Status.FAILED
                return task
            result = await self._execute_with_retry(task, step, last_outputs)
            if result.status != Status.SUCCESS:
                step.status = TaskStepStatus.FAILED
                step.error = result.error.message if result.error else "skill failed"
                task = await self.planner.replan(task, index)
                if self.policy.on_exhausted.value == "abort":
                    task.status = Status.FAILED
                    return task
                task.status = Status.FAILED
                return task
            step.status = TaskStepStatus.COMPLETED
            last_outputs.update(result.outputs)
            index += 1
        task.current_step = None
        task.status = Status.SUCCESS
        return task

    async def _execute_with_retry(self, task: Task, step: TaskStep, last_outputs: dict[str, Any]):
        attempts = self.policy.max_retries + 1
        last = None
        for _ in range(attempts):
            request = SkillRequest(
                task_id=task.task_id,
                skill_name=step.skill or "",
                inputs=bind_inputs(step.inputs, last_outputs),
            )
            last = await self.skills.execute(request)
            if last.status == Status.SUCCESS:
                return last
            try:
                skill = self.skills.registry.get(step.skill or "")
            except KeyError:
                skill = None
            if skill is not None:
                last = await skill.recover(request, last, self.skills.context)
                if last.status == Status.SUCCESS:
                    return last
        return last


NodeFn = Callable[[dict[str, Any]], Awaitable[str]]


class Graph:
    """Lightweight workflow graph; LangGraph can replace this adapter later."""

    def __init__(self) -> None:
        self.nodes: dict[str, NodeFn] = {}
        self.start = "understand"

    def add(self, name: str, fn: NodeFn) -> None:
        self.nodes[name] = fn

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        current = self.start
        visited: list[str] = []
        while current not in {"finish", "end"}:
            visited.append(current)
            current = await self.nodes[current](state)
            if len(visited) > 32:
                raise RuntimeError("graph exceeded iteration budget")
        state["path"] = visited
        return state


def cognition_graph(harness: AgentHarness) -> Graph:
    graph = Graph()

    async def understand(state: dict[str, Any]) -> str:
        task: Task = state["task"]
        state["goal"] = task.goal
        return "world"

    async def world(state: dict[str, Any]) -> str:
        snapshot = await harness.skills.context.world_model.snapshot()
        state["world_revision"] = snapshot.revision
        return "memory"

    async def memory(state: dict[str, Any]) -> str:
        from memory import MemoryQuery

        records = await harness.skills.context.memory.retrieve(MemoryQuery(text=state["goal"], limit=5))
        state["memories"] = len(records)
        return "plan"

    async def plan(state: dict[str, Any]) -> str:
        state["task"] = await harness.planner.plan(state["task"])
        return "execute"

    async def execute(state: dict[str, Any]) -> str:
        state["task"] = await harness.run(state["task"])
        return "monitor"

    async def monitor(state: dict[str, Any]) -> str:
        task: Task = state["task"]
        return "finish" if task.status == Status.SUCCESS else "replan"

    async def replan(state: dict[str, Any]) -> str:
        task: Task = state["task"]
        failed = task.current_step or 0
        state["task"] = await harness.planner.replan(task, failed)
        return "finish"

    graph.add("understand", understand)
    graph.add("world", world)
    graph.add("memory", memory)
    graph.add("plan", plan)
    graph.add("execute", execute)
    graph.add("monitor", monitor)
    graph.add("replan", replan)
    return graph


class ReActLoop:
    """Single-node ReAct loop over registered skills."""

    def __init__(self, skills: SkillRuntime, max_steps: int = 8) -> None:
        self.skills = skills
        self.max_steps = max_steps

    async def run(self, task: Task) -> Task:
        task.status = Status.RUNNING
        last_outputs: dict[str, Any] = {}
        for index, step in enumerate(task.steps):
            task.current_step = index
            thought = f"select skill {step.skill}"
            step.status = TaskStepStatus.RUNNING
            request = SkillRequest(
                task_id=task.task_id,
                skill_name=step.skill or "",
                inputs=bind_inputs(step.inputs, last_outputs),
            )
            result = await self.skills.execute(request)
            step.inputs = {**step.inputs, "thought": thought}
            if result.status != Status.SUCCESS:
                step.status = TaskStepStatus.FAILED
                step.error = result.error.message if result.error else "skill failed"
                task.status = Status.FAILED
                return task
            step.status = TaskStepStatus.COMPLETED
            last_outputs.update(result.outputs)
            if index >= self.max_steps:
                break
        task.status = Status.SUCCESS
        return task
