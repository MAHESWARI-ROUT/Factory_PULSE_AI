from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import (
    get_batch_prediction_service,
    get_ml_prediction_service,
    get_recommendation_service,
)
from app.domain.entities import SensorReading
from app.schemas.batch import BatchPredictionResponse
from app.schemas.machine import PredictionOut, SensorReadingIn
from app.services.batch_prediction import BatchPredictionService, UnsupportedFileTypeError
from app.services.interfaces import IMLPredictionService
from app.services.recommendation import RuleBasedRecommendationService

router = APIRouter(prefix="/predictions", tags=["predictions"])

_TEMPLATE_CSV = (
    "machine_id,machine_type,air_temperature_k,process_temperature_k,"
    "rotational_speed_rpm,torque_nm,tool_wear_min\n"
    "M-201,M,298.5,309.1,1450,42.0,15\n"
    "M-202,L,302.9,312.4,1340,68.5,210\n"
)


@router.get("/batch-template")
def download_batch_template() -> StreamingResponse:
    """A ready-to-fill CSV so uploaders know exactly which columns/units are
    expected — raw AI4I-style headers ("Air temperature [K]") are accepted
    too, this is just the friendliest default."""
    return StreamingResponse(
        io.BytesIO(_TEMPLATE_CSV.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=factorypulse_batch_template.csv"},
    )


@router.post("/batch-predict", response_model=BatchPredictionResponse)
async def batch_predict(
    file: UploadFile,
    batch_service: BatchPredictionService = Depends(get_batch_prediction_service),
) -> BatchPredictionResponse:
    """Upload a CSV/Excel export from a plant's IoT/SCADA system — one row
    per machine reading — and get a health score, failure risk, and
    recommended action back for every row in one pass."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        return batch_service.predict_from_file(file.filename or "upload", content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/predict", response_model=PredictionOut)
def predict(
    payload: SensorReadingIn,
    ml_service: IMLPredictionService = Depends(get_ml_prediction_service),
    recommendation_service: RuleBasedRecommendationService = Depends(get_recommendation_service),
) -> PredictionOut:
    """Run a one-off prediction for manually entered sensor values — useful
    for testing 'what if' scenarios without waiting for a real sensor feed."""
    reading = SensorReading(
        machine_id=payload.machine_id,
        machine_type=payload.machine_type,
        air_temperature_k=payload.air_temperature_k,
        process_temperature_k=payload.process_temperature_k,
        rotational_speed_rpm=payload.rotational_speed_rpm,
        torque_nm=payload.torque_nm,
        tool_wear_min=payload.tool_wear_min,
        recorded_at=datetime.now(timezone.utc),
    )
    outcome = ml_service.predict(reading)
    recommendation = recommendation_service.recommend(payload.machine_id, reading, outcome)

    return PredictionOut(
        failure_probability=outcome.failure_probability,
        predicted_failure_type=outcome.predicted_failure_type,
        anomaly_score=outcome.anomaly_score,
        is_anomaly=outcome.is_anomaly,
        health_score=outcome.health_score,
        health_status=outcome.health_status,
        priority=recommendation.priority,
        recommended_action=recommendation.recommended_action,
    )
