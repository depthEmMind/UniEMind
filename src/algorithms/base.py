"""Algorithm research contracts, decoupled from the robot runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from schema.inference import InferenceRequest, InferenceResponse


class Dataset(ABC):
    @abstractmethod
    def load(self) -> list[dict[str, Any]]: ...


class Model(ABC):
    name: str


class Trainer(ABC):
    @abstractmethod
    def train(self, dataset: Dataset, model: Model) -> Model: ...


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, model: Model, dataset: Dataset) -> dict[str, float]: ...


class Exporter(ABC):
    @abstractmethod
    def export(self, model: Model) -> dict[str, Any]: ...


class Inferencer(ABC):
    @abstractmethod
    async def infer(self, request: InferenceRequest) -> InferenceResponse: ...
