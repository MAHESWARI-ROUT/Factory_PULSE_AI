from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_ml_prediction_service,
    get_recommendation_service,
)
from app.domain.entities import SensorReading
from app.schemas.machine import PredictionOut, SensorReadingIn
from app.services.interfaces import IMLPredictionService
from app.services.recommendation import RuleBasedRecommendationService

router = APIRouter(prefix="/predictions", tags=["predictions"])


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
