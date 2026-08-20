"""Minimal detection pipeline used to prove the algorithm interface."""

from __future__ import annotations

from typing import Any

from algorithms.base import Dataset, Evaluator, Exporter, Inferencer, Model, Trainer
from schema.base import Status
from schema.inference import InferenceRequest, InferenceResponse


class LabelDataset(Dataset):
    def __init__(self, samples: list[dict[str, Any]]) -> None:
        self.samples = samples

    def load(self) -> list[dict[str, Any]]:
        return list(self.samples)


class LabelModel(Model):
    def __init__(self, labels: set[str] | None = None) -> None:
        self.name = "label_detector"
        self.labels = labels or set()


class LabelTrainer(Trainer):
    def train(self, dataset: Dataset, model: Model) -> Model:
        labels = {str(sample["label"]) for sample in dataset.load()}
        trained = LabelModel(labels)
        return trained


class LabelEvaluator(Evaluator):
    def evaluate(self, model: Model, dataset: Dataset) -> dict[str, float]:
        assert isinstance(model, LabelModel)
        samples = dataset.load()
        hits = sum(1 for sample in samples if sample["label"] in model.labels)
        return {"accuracy": hits / len(samples) if samples else 0.0}


class LabelExporter(Exporter):
    def export(self, model: Model) -> dict[str, Any]:
        assert isinstance(model, LabelModel)
        return {"format": "json", "labels": sorted(model.labels)}


class LabelInferencer(Inferencer):
    def __init__(self, model: LabelModel) -> None:
        self.model = model

    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        label = str(request.inputs.get("label", ""))
        found = label in self.model.labels
        return InferenceResponse(
            request_id=request.request_id,
            status=Status.SUCCESS if found else Status.FAILED,
            outputs={"found": found, "label": label},
        )
