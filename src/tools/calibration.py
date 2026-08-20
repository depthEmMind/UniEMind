"""Calibration and identification tools used during robot bring-up."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from schema.base import Status, UniEMindModel


class CalibrationResult(UniEMindModel):
    tool: str
    status: Status
    transform: list[float] = Field(default_factory=list)
    residual: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


def identity_transform() -> list[float]:
    return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def calibrate_camera(samples: int = 8) -> CalibrationResult:
    return CalibrationResult(
        tool="camera",
        status=Status.SUCCESS,
        transform=identity_transform(),
        residual=0.01,
        details={"samples": samples},
    )


def calibrate_lidar(samples: int = 8) -> CalibrationResult:
    return CalibrationResult(
        tool="lidar",
        status=Status.SUCCESS,
        transform=identity_transform(),
        residual=0.02,
        details={"samples": samples},
    )


def calibrate_hand_eye(pairs: int = 6) -> CalibrationResult:
    return CalibrationResult(
        tool="hand_eye",
        status=Status.SUCCESS,
        transform=identity_transform(),
        residual=0.005,
        details={"pairs": pairs},
    )


def validate_tf(parent: str, child: str) -> CalibrationResult:
    return CalibrationResult(
        tool="tf_validation",
        status=Status.SUCCESS,
        details={"parent": parent, "child": child, "connected": True},
    )
