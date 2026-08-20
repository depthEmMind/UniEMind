import asyncio

from agent import ReActLoop
from execution import ActionExecutor
from memory import MemoryRouter
from safety import SafetyGuard
from schema import Header, Observation, ObservedObject, Task, TaskStep
from schema.geometry import Pose
from simulation import SimulatedController
from skills import SkillContext, SkillRegistry, SkillRuntime, register_standard_skills
from world_model import WorldModel


def test_react_loop_inspects_object() -> None:
    async def scenario() -> str:
        world = WorldModel()
        await world.apply_observation(
            Observation(
                header=Header(source="test"),
                observer="front",
                objects=[ObservedObject(object_id="cup-1", label="cup", confidence=1.0, pose=Pose())],
            )
        )
        registry = SkillRegistry()
        register_standard_skills(registry, ActionExecutor(SafetyGuard(), SimulatedController(world)))
        runtime = SkillRuntime(registry, SkillContext(world, MemoryRouter()))
        task = Task(
            session_id="react",
            goal="inspect cup",
            steps=[
                TaskStep(name="find", skill="find_object", inputs={"label": "cup"}),
                TaskStep(name="inspect", skill="inspect_object", inputs={"object_id": "$last.object_id"}),
            ],
        )
        completed = await ReActLoop(runtime).run(task)
        return completed.status.value

    assert asyncio.run(scenario()) == "SUCCESS"
