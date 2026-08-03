"""Seeds the database from the AI4I 2020 dataset. The raw dataset has 10,000
independent product rows; to make a believable "fleet of machines monitored
over time" for the dashboard, rows are round-robined across a configurable
number of synthetic machine IDs (M-101, M-102, ...), each becoming a
timestamped reading in that machine's history. This is a one-time,
idempotent operation — re-running it on an already-seeded DB is a no-op.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from app.domain.entities import SensorReading
from app.domain.enums import MachineType
from app.orm.models import MachineSnapshot
from app.repositories.interfaces import IMachineRepository, ISnapshotRepository
from app.services.interfaces import IMLPredictionService, IRecommendationService

logger = logging.getLogger("factorypulse.seeder")


class DataSeederService:
    def __init__(
        self,
        machine_repo: IMachineRepository,
        snapshot_repo: ISnapshotRepository,
        ml_service: IMLPredictionService,
        recommendation_service: IRecommendationService,
    ):
        self._machine_repo = machine_repo
        self._snapshot_repo = snapshot_repo
        self._ml_service = ml_service
        self._recommendation_service = recommendation_service

    def seed_from_csv(
        self, csv_path: Path, num_machines: int = 40, max_rows: int = 4000
    ) -> int:
        if self._machine_repo.count() > 0:
            logger.info("Database already seeded (%d machines) — skipping.", self._machine_repo.count())
            return 0

        df = pd.read_csv(csv_path).head(max_rows)
        logger.info("Seeding database from %d rows across %d synthetic machines", len(df), num_machines)

        now = datetime.now(timezone.utc)
        inserted = 0
        for i, row in df.iterrows():
            machine_index = int(row["UDI"]) % num_machines
            machine_id = f"M-{101 + machine_index}"
            machine_type = str(row["Type"])
            machine = self._machine_repo.get_or_create(machine_id, machine_type)

            reading = SensorReading(
                machine_id=machine_id,
                machine_type=MachineType(machine_type),
                air_temperature_k=float(row["Air temperature [K]"]),
                process_temperature_k=float(row["Process temperature [K]"]),
                rotational_speed_rpm=float(row["Rotational speed [rpm]"]),
                torque_nm=float(row["Torque [Nm]"]),
                tool_wear_min=float(row["Tool wear [min]"]),
                recorded_at=now - timedelta(minutes=(len(df) - i) * 5),
            )
            outcome = self._ml_service.predict(reading)
            recommendation = self._recommendation_service.recommend(machine_id, reading, outcome)

            snapshot = MachineSnapshot(
                air_temperature_k=reading.air_temperature_k,
                process_temperature_k=reading.process_temperature_k,
                rotational_speed_rpm=reading.rotational_speed_rpm,
                torque_nm=reading.torque_nm,
                tool_wear_min=reading.tool_wear_min,
                failure_probability=outcome.failure_probability,
                predicted_failure_type=outcome.predicted_failure_type.value,
                anomaly_score=outcome.anomaly_score,
                is_anomaly=outcome.is_anomaly,
                health_score=outcome.health_score,
                health_status=outcome.health_status,
                priority=recommendation.priority.value,
                recommended_action=recommendation.recommended_action,
                recorded_at=reading.recorded_at,
            )
            self._snapshot_repo.add(machine, snapshot)
            inserted += 1

        logger.info("Seeding complete: %d snapshots inserted.", inserted)
        return inserted
