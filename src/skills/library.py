"""Reusable skill implementations used by both MVP loops."""

from __future__ import annotations

from execution import ActionExecutor
from schema import (
    ActionRequest,
    ActionType,
    ErrorCode,
    ErrorDetail,
    SkillMetadata,
    SkillRequest,
    SkillResult,
    Status,
)
from skills.runtime import Skill, SkillContext


def skill_failure(request: SkillRequest, code: ErrorCode, message: str) -> SkillResult:
    return SkillResult(
        execution_id=request.execution_id,
        status=Status.FAILED,
        error=ErrorDetail(code=code, message=message),
    )


class FindObjectSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="find_object", version="v1", category="perception")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        label = str(request.inputs["label"])
        found = await context.world_model.find_by_label(label)
        if found is None:
            return skill_failure(request, ErrorCode.NOT_FOUND, f"no {label} in world model")
        return SkillResult(
            execution_id=request.execution_id,
            status=Status.SUCCESS,
            outputs={"object_id": found.object_id},
        )


class InspectObjectSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="inspect_object", version="v1", category="perception")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        observed = await context.world_model.get_object(str(request.inputs["object_id"]))
        if observed is None:
            return skill_failure(request, ErrorCode.NOT_FOUND, "object missing")
        return SkillResult(
            execution_id=request.execution_id,
            status=Status.SUCCESS,
            outputs={"label": observed.label, "attributes": observed.attributes},
        )


class SpeakSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="speak", version="v1", category="interaction")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        return SkillResult(
            execution_id=request.execution_id,
            status=Status.SUCCESS,
            outputs={"utterance": str(request.inputs.get("text", ""))},
        )


class VerifyGraspSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="verify_grasp", version="v1", category="perception")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        observed = await context.world_model.get_object(str(request.inputs["object_id"]))
        if observed is None or not observed.attributes.get("grasped"):
            return skill_failure(request, ErrorCode.EXECUTION_FAILED, "grasp verification failed")
        return SkillResult(execution_id=request.execution_id, status=Status.SUCCESS)


class VerifyPourSkill(Skill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="verify_pour", version="v1", category="perception")

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        observed = await context.world_model.get_object(str(request.inputs["object_id"]))
        if observed is None or not observed.attributes.get("poured"):
            return skill_failure(request, ErrorCode.EXECUTION_FAILED, "pour verification failed")
        return SkillResult(execution_id=request.execution_id, status=Status.SUCCESS)


class ActionSkill(Skill):
    target: str
    name: str
    category: str = "manipulation"

    def __init__(self, executor: ActionExecutor) -> None:
        self.executor = executor

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name=self.name, version="v1", category=self.category)

    async def execute(self, request: SkillRequest, context: SkillContext) -> SkillResult:
        command = dict(request.inputs)
        action = ActionRequest(
            task_id=request.task_id,
            execution_id=request.execution_id,
            action_type=ActionType.CONTROLLER,
            target=self.target,
            command=command,
        )
        result = await self.executor.execute(action)
        return SkillResult(
            execution_id=request.execution_id,
            status=result.status,
            outputs=result.feedback or command,
            error=result.error,
        )


class NavigateToObjectSkill(ActionSkill):
    target = "navigate_to_object"
    name = "navigate_to_object"
    category = "navigation"


class NavigateToLocationSkill(ActionSkill):
    target = "navigate_to_location"
    name = "navigate_to"
    category = "navigation"


class FollowSkill(ActionSkill):
    target = "follow_target"
    name = "follow"
    category = "navigation"


class ReachSkill(ActionSkill):
    target = "reach_object"
    name = "reach"


class GraspObjectSkill(ActionSkill):
    target = "grasp_object"
    name = "grasp_object"


class PickSkill(ActionSkill):
    target = "grasp_object"
    name = "pick"


class PlaceSkill(ActionSkill):
    target = "place_object"
    name = "place"


class PourSkill(ActionSkill):
    target = "pour_object"
    name = "pour"


def register_standard_skills(registry: object, executor: ActionExecutor) -> None:
    from skills.runtime import SkillRegistry

    assert isinstance(registry, SkillRegistry)
    for skill in (
        FindObjectSkill(),
        InspectObjectSkill(),
        SpeakSkill(),
        VerifyGraspSkill(),
        VerifyPourSkill(),
        NavigateToObjectSkill(executor),
        NavigateToLocationSkill(executor),
        FollowSkill(executor),
        ReachSkill(executor),
        GraspObjectSkill(executor),
        PickSkill(executor),
        PlaceSkill(executor),
        PourSkill(executor),
    ):
        registry.register(skill)
