"""Turns a prediction into an actionable maintenance recommendation: a
priority level and a concrete next step. Deliberately rule-based and
deterministic — plant managers need to trust and audit *why* something is
flagged urgent, which a black-box LLM call shouldn't be the sole source of."""
from __future__ import annotations

from app.domain.entities import MaintenanceRecommendation, PredictionOutcome, SensorReading
from app.domain.enums import FailureType, HealthStatus, MaintenancePriority
from app.services.interfaces import IRecommendationService

_ACTION_BY_FAILURE_TYPE = {
    FailureType.HEAT_DISSIPATION_FAILURE: (
        "Inspect cooling system and airflow; verify process-to-air temperature "
        "differential is within spec."
    ),
    FailureType.POWER_FAILURE: (
        "Check power supply stability and motor load; measure torque against "
        "rated rotational speed."
    ),
    FailureType.OVERSTRAIN_FAILURE: (
        "Reduce load or feed rate; inspect for mechanical strain on the tool "
        "and spindle assembly."
    ),
    FailureType.TOOL_WEAR_FAILURE: (
        "Schedule tool replacement; current tool wear is approaching the "
        "failure threshold."
    ),
    FailureType.RANDOM_FAILURE: (
        "No clear root cause signal; add this machine to the next routine "
        "inspection round."
    ),
    FailureType.NONE: "No action required. Continue standard monitoring cadence.",
}


class RuleBasedRecommendationService(IRecommendationService):
    def recommend(
        self, machine_id: str, reading: SensorReading, outcome: PredictionOutcome
    ) -> MaintenanceRecommendation:
        priority = self._priority_for(outcome)
        action = _ACTION_BY_FAILURE_TYPE[outcome.predicted_failure_type]
        if priority == MaintenancePriority.URGENT:
            action = f"{action} Schedule maintenance within the next shift."

        explanation = self._build_explanation(machine_id, reading, outcome)
        return MaintenanceRecommendation(
            machine_id=machine_id,
            priority=priority,
            recommended_action=action,
            explanation=explanation,
        )

    @staticmethod
    def _priority_for(outcome: PredictionOutcome) -> MaintenancePriority:
        if outcome.health_status == HealthStatus.CRITICAL.value:
            return MaintenancePriority.URGENT
        if outcome.health_status == HealthStatus.WARNING.value:
            return MaintenancePriority.HIGH
        if outcome.is_anomaly:
            return MaintenancePriority.MEDIUM
        return MaintenancePriority.LOW

    @staticmethod
    def _build_explanation(machine_id: str, reading: SensorReading, outcome: PredictionOutcome) -> str:
        if outcome.predicted_failure_type == FailureType.NONE:
            return (
                f"{machine_id} is operating within normal parameters "
                f"(health score {outcome.health_score:.0f})."
            )
        temp_delta = reading.process_temperature_k - reading.air_temperature_k
        return (
            f"{machine_id} shows a {outcome.failure_probability * 100:.0f}% probability of "
            f"{outcome.predicted_failure_type.display_name} based on a process/air temperature "
            f"differential of {temp_delta:.1f}K, tool wear of {reading.tool_wear_min:.0f} min, "
            f"and torque of {reading.torque_nm:.1f} Nm."
        )
