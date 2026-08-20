# Foundation architecture

UniEMind's first stable boundary is schema-first and transport-neutral.

```text
ROS 2 driver -> SensorAdapter -> SensorData -> DataBus
                                      |-> Perception
                                      |-> World Model
                                      |-> Recorder / Logger

Agent -> SkillRequest -> ActionRequest -> Safety -> Controller -> ROS2Transport
```

The cognitive core never imports `rclpy` and never receives vendor-specific messages. A deployment
package implements `ROS2Transport` and sensor adapters. Every public protocol carries a versioned
header or API envelope. Existing `v1` schemas are extended compatibly; breaking changes require a
new protocol version.

## Configuration precedence

Lowest to highest priority: YAML/JSON file, `UNIEMIND_` environment variables, explicit runtime
or CLI overrides. Nested environment keys use double underscores, for example
`UNIEMIND_SENSORS__RGB_CAMERA=false`.

## Safety invariant

`ActionRequest.requires_safety_check` defaults to true. Runtime execution must reject unchecked
actions; the concrete safety runtime is delivered in the Skill/Execution phase.
