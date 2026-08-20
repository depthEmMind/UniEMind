# Runtime layers

After the Foundation schemas, UniEMind adds replaceable runtimes that keep data flow and control flow separate.

```text
Sensor -> Adapter -> DataBus -> Perception -> World Model
User -> Interaction -> Session -> Agent Graph -> Skill -> Safety -> Controller -> ROS2 transport
Robot -> Observation -> Monitor -> Evaluate -> Replan
```

## Agent graph

`cognition_graph` implements the specification node sequence without importing LangGraph:

understand -> world query -> memory -> plan -> execute -> monitor -> finish | replan

`ReActLoop` is a single-node alternative. `GoalPlanner` currently covers the two closed-loop tasks from the specification. A LangGraph adapter can wrap the same node functions later.

## Safety

Every `ActionRequest` still defaults to `requires_safety_check=true`. The guard also enforces velocity, workspace, joint, battery, collision, timeout, and emergency-stop constraints.

## Algorithm platform

Training code lives under `src/algorithms` and only talks to the runtime through
`InferenceRequest` / `InferenceResponse`. The detection package is a complete
Dataset -> Train -> Eval -> Export -> Infer slice; other algorithm folders are
extension points.
