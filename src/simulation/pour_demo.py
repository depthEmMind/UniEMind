"""Second specification closed loop: lab bench -> cup -> sink -> pour."""

from __future__ import annotations

from agent import AgentHarness, GoalPlanner, cognition_graph
from execution import ActionExecutor
from memory import MemoryKind, MemoryRecord, MemoryRouter
from safety import SafetyGuard
from schema import Header, Observation, ObservedObject, Task
from schema.geometry import Pose, Vector3
from simulation.controller import SimulatedController
from skills import SkillContext, SkillRegistry, SkillRuntime, register_standard_skills
from world_model import WorldModel


async def build_pour_demo() -> tuple[AgentHarness, Task, WorldModel, MemoryRouter]:
    world_model = WorldModel()
    await world_model.set_location("lab_bench", Pose(position=Vector3(x=1.2, y=0.4, z=0.0), frame_id="map"))
    await world_model.set_location("sink", Pose(position=Vector3(x=2.5, y=0.1, z=0.0), frame_id="map"))
    await world_model.apply_observation(
        Observation(
            header=Header(source="simulated_detector", frame_id="map"),
            observer="front_camera",
            objects=[
                ObservedObject(
                    object_id="cup-1",
                    label="cup",
                    confidence=0.97,
                    pose=Pose(position=Vector3(x=1.2, y=0.4, z=0.8), frame_id="map"),
                    attributes={
                        "support_surface": "lab_bench",
                        "grasped": False,
                        "contains_liquid": True,
                    },
                )
            ],
        )
    )

    memory = MemoryRouter()
    await memory.remember(
        MemoryRecord(
            kind=MemoryKind.SEMANTIC,
            content={"fact": "cups are usually on the lab bench"},
            tags={"cup", "lab_bench"},
        )
    )
    await memory.remember(
        MemoryRecord(
            kind=MemoryKind.WORKING,
            content={"task": "pour water into the sink"},
            tags={"pour"},
        )
    )

    executor = ActionExecutor(SafetyGuard(), SimulatedController(world_model))
    registry = SkillRegistry()
    register_standard_skills(registry, executor)
    runtime = SkillRuntime(registry, SkillContext(world_model, memory))
    task = Task(
        session_id="pour-session",
        goal="navigate to the lab bench, find the cup, grasp it, move to the sink, pour, and verify success",
    )
    return AgentHarness(GoalPlanner(), runtime), task, world_model, memory


async def run_pour_demo() -> tuple[Task, WorldModel]:
    harness, task, world_model, _ = await build_pour_demo()
    graph = cognition_graph(harness)
    state = await graph.run({"task": task})
    return state["task"], world_model
