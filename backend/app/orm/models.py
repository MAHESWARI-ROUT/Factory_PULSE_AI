"""ORM layer. Two tables are enough to model the domain:

  Machine          - one row per physical asset on the floor
  MachineSnapshot   - one row per sensor reading + the prediction computed for it

A snapshot is immutable once written (it represents "what the sensors said
and what the model concluded at time T"), so the current state of a machine
is always "its most recent snapshot", not a column that gets mutated in place.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    machine_type: Mapped[str] = mapped_column(String(1))  # L / M / H
    location: Mapped[str] = mapped_column(String(64), default="Plant Floor")
    installed_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    snapshots: Mapped[list["MachineSnapshot"]] = relationship(
        back_populates="machine", cascade="all, delete-orphan", order_by="MachineSnapshot.recorded_at"
    )


class MachineSnapshot(Base):
    __tablename__ = "machine_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_db_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True)

    # Raw sensor values
    air_temperature_k: Mapped[float] = mapped_column(Float)
    process_temperature_k: Mapped[float] = mapped_column(Float)
    rotational_speed_rpm: Mapped[float] = mapped_column(Float)
    torque_nm: Mapped[float] = mapped_column(Float)
    tool_wear_min: Mapped[float] = mapped_column(Float)

    # Model outputs
    failure_probability: Mapped[float] = mapped_column(Float)
    predicted_failure_type: Mapped[str] = mapped_column(String(8))
    anomaly_score: Mapped[float] = mapped_column(Float)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    health_score: Mapped[float] = mapped_column(Float)
    health_status: Mapped[str] = mapped_column(String(16))
    priority: Mapped[str] = mapped_column(String(16))
    recommended_action: Mapped[str] = mapped_column(String(512))

    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=_utcnow)

    machine: Mapped["Machine"] = relationship(back_populates="snapshots")
