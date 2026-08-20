"""Deterministic simulation of the first specification MVP cup task."""

from __future__ import annotations

from uniemind.agent import AgentHarness, StaticPlanner
from uniemind.execution import ActionExecutor, Controller
from uniemind.memory import MemoryKind, MemoryRecord, MemoryRouter
from uniemind.safety import SafetyGuard
from uniemind.schema import (
    ActionRequest,
    ActionResult,
    ActionType,
    ErrorCode,
    ErrorDetail,
    Header,
    Observation,
    ObservedObject,
    RobotState,
    SkillMetadata,
    SkillRequest,
    SkillResult,
    Status,
    Task,
    TaskStep,
)
from uniemind.schema.geometry import Pose, Vector3
from uniemind.skills import Skill, SkillContext, SkillRegistry, SkillRuntime
from uniemind.world_model import WorldModel


class SimulatedController(Controller):
    def __init__(self, world_model: WorldModel) -> None:
        self.world_model = world_model
        self.cancelled: set[str] = set()

    async def execute(self, request: ActionRequest) -> ActionResult:
        object_id = str(request.command.get("object_id", ""))
        observed = await self.world_model.get_object(object_id)
        if observed is None:
            return ActionResult(
                action_id=request.action_id,
                status=Status.FAILED,
                error=ErrorDetail(code=ErrorCode.NOT_FOUND, message=f"object not found: {object_id}"),
            )
        if request.target == "navigate_to_object":
            robot = RobotState(
                header=Header(source="simulation", frame_id="map"),
                pose=observed.pose or Pose(frame_id="map"),
                controller_state=Status.READY,
            )
            await self.world_model.set_robot_state(robot)
        elif request.target == "grasp_object":
            observed.attributes["grasped"] = True
            observed.attributes["held_by"] = "demo_robot"
            await self.world_model.upsert_object(observed)
        else:
            return ActionResult(
                action_id=request.action_id,
                status=Status.FAILED,
                error=ErrorDetail(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"unsupported simulated action: {request.target}",
                ),
            )
        return ActionResult(action_id=request.action_id, status=Status.SUCCESS)

    async def cancel(self, action_id: str) -> None:
        self.cancelled.add(action_id)


class FindObjectSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="find_object", version="v1", category="perception")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        label = str(request.inputs["label"])
        state = await context.world_model.snapshot()
        found = next((item for item in state.objects.values() if item.label == label), None)
        if found is None:
            return _skill_failure(request, ErrorCode.NOT_FOUND, f"no {label} in world model")
        return SkillResult(
            execution_id=request.execution_id,
            status=Status.SUCCESS,
            outputs={"object_id": found.object_id},
        )


class ActionSkill(Skill):
    target: str
    name: str

    def __init__(self, executor: ActionExecutor) -> None:
        self.executor = executor

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name=self.name, version="v1", category="manipulation")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        action = ActionRequest(
            task_id=request.task_id,
            execution_id=request.execution_id,
            action_type=ActionType.CONTROLLER,
            target=self.target,
            command={"object_id": request.inputs["object_id"]},
        )
        result = await self.executor.execute(action)
        return SkillResult(
            execution_id=request.execution_id,
            status=result.status,
            outputs=result.feedback,
            error=result.error,
        )


class NavigateToObjectSkill(ActionSkill):
    target = "navigate_to_object"
    name = "navigate_to_object"


class GraspObjectSkill(ActionSkill):
    target = "grasp_object"
    name = "grasp_object"


class VerifyGraspSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="verify_grasp", version="v1", category="perception")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        observed = await context.world_model.get_object(str(request.inputs["object_id"]))
        if observed is None or not observed.attributes.get("grasped"):
            return _skill_failure(request, ErrorCode.EXECUTION_FAILED, "grasp verification failed")
        return SkillResult(execution_id=request.execution_id, status=Status.SUCCESS)


def _skill_failure(request: SkillRequest, code: ErrorCode, message: str) -> SkillResult:
    return SkillResult(
        execution_id=request.execution_id,
        status=Status.FAILED,
        error=ErrorDetail(code=code, message=message),
    )


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
    registry.register(FindObjectSkill())
    registry.register(NavigateToObjectSkill(executor))
    registry.register(GraspObjectSkill(executor))
    registry.register(VerifyGraspSkill())
    runtime = SkillRuntime(registry, SkillContext(world_model, memory))

    task = Task(
        session_id="demo-session",
        goal="find the cup on the table, approach it, grasp it, and verify success",
        steps=[
            TaskStep(name="find cup", skill="find_object", inputs={"label": "cup"}),
            TaskStep(
                name="approach table", skill="navigate_to_object", inputs={"object_id": "cup-1"}
            ),
            TaskStep(name="grasp cup", skill="grasp_object", inputs={"object_id": "cup-1"}),
            TaskStep(name="verify grasp", skill="verify_grasp", inputs={"object_id": "cup-1"}),
        ],
    )
    return AgentHarness(StaticPlanner(), runtime), task, world_model, memory


async def run_cup_demo() -> tuple[Task, WorldModel]:
    harness, task, world_model, _ = await build_cup_demo()
    return await harness.run(task), world_model
