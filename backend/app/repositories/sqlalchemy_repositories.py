from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.orm.models import Machine, MachineSnapshot
from app.repositories.interfaces import IMachineRepository, ISnapshotRepository


class SqlAlchemyMachineRepository(IMachineRepository):
    def __init__(self, db: Session):
        self._db = db

    def get_or_create(self, machine_id: str, machine_type: str) -> Machine:
        existing = self.get_by_machine_id(machine_id)
        if existing:
            return existing
        machine = Machine(machine_id=machine_id, machine_type=machine_type)
        self._db.add(machine)
        self._db.commit()
        self._db.refresh(machine)
        return machine

    def get_by_machine_id(self, machine_id: str) -> Machine | None:
        stmt = select(Machine).where(Machine.machine_id == machine_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Machine]:
        stmt = select(Machine).order_by(Machine.machine_id)
        return list(self._db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self._db.execute(select(func.count(Machine.id))).scalar_one()


class SqlAlchemySnapshotRepository(ISnapshotRepository):
    def __init__(self, db: Session):
        self._db = db

    def add(self, machine: Machine, snapshot: MachineSnapshot) -> MachineSnapshot:
        snapshot.machine_db_id = machine.id
        self._db.add(snapshot)
        self._db.commit()
        self._db.refresh(snapshot)
        return snapshot

    def latest_for_machine(self, machine_db_id: int) -> MachineSnapshot | None:
        stmt = (
            select(MachineSnapshot)
            .where(MachineSnapshot.machine_db_id == machine_db_id)
            .order_by(MachineSnapshot.recorded_at.desc())
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def history_for_machine(self, machine_db_id: int, limit: int = 50) -> list[MachineSnapshot]:
        stmt = (
            select(MachineSnapshot)
            .where(MachineSnapshot.machine_db_id == machine_db_id)
            .order_by(MachineSnapshot.recorded_at.desc())
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())

    def latest_per_machine(self) -> list[MachineSnapshot]:
        # Sub-select the max recorded_at per machine, then join back to get
        # the full row. Portable across SQLite (dev) and Postgres (prod).
        latest_ts_subq = (
            select(
                MachineSnapshot.machine_db_id,
                func.max(MachineSnapshot.recorded_at).label("max_recorded_at"),
            )
            .group_by(MachineSnapshot.machine_db_id)
            .subquery()
        )
        stmt = select(MachineSnapshot).join(
            latest_ts_subq,
            (MachineSnapshot.machine_db_id == latest_ts_subq.c.machine_db_id)
            & (MachineSnapshot.recorded_at == latest_ts_subq.c.max_recorded_at),
        )
        return list(self._db.execute(stmt).scalars().all())

    def snapshots_since(self, since: datetime) -> list[MachineSnapshot]:
        stmt = select(MachineSnapshot).where(MachineSnapshot.recorded_at >= since)
        return list(self._db.execute(stmt).scalars().all())
