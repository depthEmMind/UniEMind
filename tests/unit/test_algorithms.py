import asyncio

from algorithms.detection import (
    LabelDataset,
    LabelEvaluator,
    LabelExporter,
    LabelInferencer,
    LabelModel,
    LabelTrainer,
)
from schema import InferenceRequest, Status


def test_detection_pipeline_train_export_infer() -> None:
    dataset = LabelDataset([{"label": "cup"}, {"label": "bowl"}])
    model = LabelTrainer().train(dataset, LabelModel())
    metrics = LabelEvaluator().evaluate(model, dataset)
    exported = LabelExporter().export(model)
    response = asyncio.run(
        LabelInferencer(model).infer(InferenceRequest(model_id="label_detector", inputs={"label": "cup"}))
    )
    assert metrics["accuracy"] == 1.0
    assert exported["labels"] == ["bowl", "cup"]
    assert response.status == Status.SUCCESS
