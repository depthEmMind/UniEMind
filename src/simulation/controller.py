"""Shared simulated robot controller used by specification closed loops."""

from __future__ import annotations

from execution import Controller
from schema import ActionRequest, ActionResult, ErrorCode, ErrorDetail, Header, RobotState, Status
from schema.geometry import Pose
from world_model import WorldModel


class SimulatedController(Controller):
    def __init__(self, world_model: WorldModel, robot_name: str = "demo_robot") -> None:
        self.world_model = world_model
        self.robot_name = robot_name
        self.cancelled: set[str] = set()

    async def execute(self, request: ActionRequest) -> ActionResult:
        target = request.target
        if target == "navigate_to_location":
            return await self._navigate_location(request)
        if target == "navigate_to_object":
            return await self._navigate_object(request)
        if target in {"grasp_object", "reach_object", "follow_target", "place_object", "pour_object"}:
            return await self._object_action(request, target)
        return ActionResult(
            action_id=request.action_id,
            status=Status.FAILED,
            error=ErrorDetail(code=ErrorCode.INVALID_INPUT, message=f"unsupported action: {target}"),
        )

    async def cancel(self, action_id: str) -> None:
        self.cancelled.add(action_id)

    async def _navigate_location(self, request: ActionRequest) -> ActionResult:
        location = str(request.command.get("location", ""))
        state = await self.world_model.snapshot()
        pose = state.locations.get(location)
        if pose is None:
            return self._fail(request, ErrorCode.NOT_FOUND, f"unknown location: {location}")
        await self.world_model.set_robot_state(
            RobotState(
                header=Header(source="simulation", frame_id="map"),
                pose=pose,
                controller_state=Status.READY,
            )
        )
        return ActionResult(
            action_id=request.action_id,
            status=Status.SUCCESS,
            feedback={"location": location},
        )

    async def _navigate_object(self, request: ActionRequest) -> ActionResult:
        observed = await self._require_object(request)
        if isinstance(observed, ActionResult):
            return observed
        await self.world_model.set_robot_state(
            RobotState(
                header=Header(source="simulation", frame_id="map"),
                pose=observed.pose or Pose(frame_id="map"),
                controller_state=Status.READY,
            )
        )
        return ActionResult(
            action_id=request.action_id,
            status=Status.SUCCESS,
            feedback={"object_id": observed.object_id},
        )

    async def _object_action(self, request: ActionRequest, target: str) -> ActionResult:
        observed = await self._require_object(request)
        if isinstance(observed, ActionResult):
            return observed
        if target in {"grasp_object", "reach_object"}:
            observed.attributes["grasped"] = True
            observed.attributes["held_by"] = self.robot_name
        elif target == "place_object":
            observed.attributes["grasped"] = False
            observed.attributes["held_by"] = None
            observed.attributes["placed"] = True
        elif target == "pour_object":
            if not observed.attributes.get("grasped"):
                return self._fail(request, ErrorCode.EXECUTION_FAILED, "cannot pour without grasp")
            observed.attributes["poured"] = True
            observed.attributes["contains_liquid"] = False
        elif target == "follow_target":
            observed.attributes["followed"] = True
        await self.world_model.upsert_object(observed)
        return ActionResult(
            action_id=request.action_id,
            status=Status.SUCCESS,
            feedback={"object_id": observed.object_id, "target": target},
        )

    async def _require_object(self, request: ActionRequest):
        object_id = str(request.command.get("object_id") or "")
        observed = await self.world_model.get_object(object_id)
        if observed is None:
            return self._fail(request, ErrorCode.NOT_FOUND, f"object not found: {object_id}")
        return observed

    @staticmethod
    def _fail(request: ActionRequest, code: ErrorCode, message: str) -> ActionResult:
        return ActionResult(
            action_id=request.action_id,
            status=Status.FAILED,
            error=ErrorDetail(code=code, message=message),
        )
