"""Sensor-to-standard-message adapters that do not import ROS 2."""

from __future__ import annotations

from typing import Any

from ros2.interfaces import SensorAdapter
from schema import Header, SensorData, SensorDataType
from schema.robot import JointState as RobotJointState
from schema.sensor import ImagePayload, IMUPayload


class DictImageAdapter(SensorAdapter[dict[str, Any]]):
    def adapt(self, message: dict[str, Any]) -> SensorData:
        payload = ImagePayload(
            width=int(message["width"]),
            height=int(message["height"]),
            encoding=str(message.get("encoding", "rgb8")),
            step=int(message.get("step", int(message["width"]) * 3)),
            data=bytes(message.get("data", b"")),
        )
        return SensorData(
            header=Header(
                source=str(message.get("source", "camera")),
                frame_id=str(message.get("frame_id", "camera_link")),
                sequence=int(message.get("sequence", 0)),
            ),
            sensor_id=str(message.get("sensor_id", "camera_front")),
            data_type=SensorDataType.IMAGE,
            payload=payload,
        )


class DictJointAdapter(SensorAdapter[dict[str, Any]]):
    def adapt(self, message: dict[str, Any]) -> SensorData:
        joints = RobotJointState(
            names=list(message.get("names", [])),
            positions=list(message.get("positions", [])),
            velocities=list(message.get("velocities", [])),
            efforts=list(message.get("efforts", [])),
        )
        return SensorData(
            header=Header(source=str(message.get("source", "robot")), frame_id="base_link"),
            sensor_id=str(message.get("sensor_id", "joints")),
            data_type=SensorDataType.JOINT_STATE,
            payload=joints,
        )


class DictIMUAdapter(SensorAdapter[dict[str, Any]]):
    def adapt(self, message: dict[str, Any]) -> SensorData:
        return SensorData(
            header=Header(source=str(message.get("source", "imu")), frame_id="imu_link"),
            sensor_id=str(message.get("sensor_id", "imu")),
            data_type=SensorDataType.IMU,
            payload=IMUPayload(),
        )
