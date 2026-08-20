"""Deterministic simulation of the first specification MVP cup task."""

from __future__ import annotations

from agent import AgentHarness, StaticPlanner
from execution import ActionExecutor
from memory import MemoryKind, MemoryRecord, MemoryRouter
from safety import SafetyGuard
from schema import Header, Observation, ObservedObject, Task, TaskStep
from schema.geometry import Pose, Vector3
from simulation.controller import SimulatedController
from skills import SkillContext, SkillRegistry, SkillRuntime, register_standard_skills
from world_model import WorldModel


async def build_cup_demo() -> tuple[AgentHarness, Task, WorldModel, MemoryRouter]:
    world_model = WorldModel()
    observation = Observation(
        header=Header(source="simulated_detector", frame_id="map"),
        observer="front_camera",
        objects=[
            ObservedObject(
                object_id="cup-1",
                label="cup",
                confidence=0.99,
                pose=Pose(position=Vector3(x=1.2, y=0.4, z=0.8), frame_id="map"),
                attributes={"support_surface": "table", "grasped": False},
            )
        ],
    )
    await world_model.apply_observation(observation)

    memory = MemoryRouter()
    await memory.remember(
        MemoryRecord(
            kind=MemoryKind.CAPABILITY,
            content={"object": "cup", "skill": "grasp_object", "approach": "side"},
            tags={"cup", "grasp"},
        )
    )

    executor = ActionExecutor(SafetyGuard(), SimulatedController(world_model))
    registry = SkillRegistry()
    register_standard_skills(registry, executor)
    runtime = SkillRuntime(registry, SkillContext(world_model, memory))

    task = Task(
        session_id="demo-session",
        goal="find the cup on the table, approach it, grasp it, and verify success",
        steps=[
            TaskStep(name="find cup", skill="find_object", inputs={"label": "cup"}),
            TaskStep(
                name="approach table",
                skill="navigate_to_object",
                inputs={"object_id": "$last.object_id"},
            ),
            TaskStep(name="grasp cup", skill="grasp_object", inputs={"object_id": "$last.object_id"}),
            TaskStep(name="verify grasp", skill="verify_grasp", inputs={"object_id": "$last.object_id"}),
        ],
    )
    return AgentHarness(StaticPlanner(), runtime), task, world_model, memory


async def run_cup_demo() -> tuple[Task, WorldModel]:
    harness, task, world_model, _ = await build_cup_demo()
    return await harness.run(task), world_model
