# Contributing

1. Keep schemas versioned. Do not break `v1` in place.
2. Upper layers must not import `rclpy` or vendor SDKs. Use adapters and `ROS2Transport`.
3. Agent code must not send joint or motor commands. Go through Skill -> Safety -> Controller.
4. Add unit or integration tests for every new module.
5. Prefer simulation-first demos before real-robot adapters.
