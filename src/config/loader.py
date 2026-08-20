"""Configuration loading with file, environment, and explicit override precedence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

ConfigT = TypeVar("ConfigT", bound=BaseModel)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _environment(prefix: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    marker = f"{prefix}_"
    for name, raw_value in os.environ.items():
        if not name.startswith(marker):
            continue
        path = name[len(marker):].lower().split("__")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        cursor = result
        for part in path[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[path[-1]] = value
    return result


def load_config(
    path: str | Path,
    model: type[ConfigT],
    *,
    env_prefix: str = "UNIEMIND",
    overrides: dict[str, Any] | None = None,
) -> ConfigT:
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as stream:
        if config_path.suffix.lower() == ".json":
            raw = json.load(stream)
        elif config_path.suffix.lower() in {".yaml", ".yml"}:
            raw = yaml.safe_load(stream) or {}
        else:
            raise ValueError(f"unsupported config format: {config_path.suffix}")
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a mapping")
    merged = _deep_merge(raw, _environment(env_prefix))
    merged = _deep_merge(merged, overrides or {})
    return model.model_validate(merged)
