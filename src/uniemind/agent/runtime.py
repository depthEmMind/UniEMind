"""Framework-neutral planning and task harness."""

from __future__ import annotations

from abc import ABC, abstractmethod

from uniemind.schema import SkillRequest, Status, Task, TaskStepStatus
from uniemind.skills import SkillRuntime


class Planner(ABC):
    @abstractmethod
    async def plan(self, task: Task) -> Task: ...

    async def replan(self, task: Task, failed_step: int) -> Task:
        return task


class StaticPlanner(Planner):
    async def plan(self, task: Task) -> Task:
        if not task.steps:
            raise ValueError("static planner requires pre-populated task steps")
        return task


class AgentHarness:
    """Runs Plan -> Skill -> Monitor/Evaluate with one recovery/replan opportunity."""

    def __init__(self, planner: Planner, skills: SkillRuntime) -> None:
        self.planner = planner
        self.skills = skills

    async def run(self, task: Task) -> Task:
        task = await self.planner.plan(task)
        task.status = Status.RUNNING
        for index, step in enumerate(task.steps):
            task.current_step = index
            step.status = TaskStepStatus.RUNNING
            if not step.skill:
                step.status = TaskStepStatus.FAILED
                step.error = "task step has no skill"
                task.status = Status.FAILED
                return task
            request = SkillRequest(
                task_id=task.task_id,
                skill_name=step.skill,
                inputs=step.inputs,
            )
            result = await self.skills.execute(request)
            if result.status != Status.SUCCESS:
                step.status = TaskStepStatus.FAILED
                step.error = result.error.message if result.error else "skill failed"
                task = await self.planner.replan(task, index)
                task.status = Status.FAILED
                return task
            step.status = TaskStepStatus.COMPLETED
        task.current_step = None
        task.status = Status.SUCCESS
        return task
