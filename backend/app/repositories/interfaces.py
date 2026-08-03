"""Abstract repository contracts. Services depend on these, never on
SQLAlchemy directly (Dependency Inversion Principle) — swapping Postgres for
another store later means writing a new class here, not touching services."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.orm.models import Machine, MachineSnapshot


class IMachineRepository(ABC):
    @abstractmethod
    def get_or_create(self, machine_id: str, machine_type: str) -> Machine: ...

    @abstractmethod
    def get_by_machine_id(self, machine_id: str) -> Machine | None: ...

    @abstractmethod
    def list_all(self) -> list[Machine]: ...

    @abstractmethod
    def count(self) -> int: ...


class ISnapshotRepository(ABC):
    @abstractmethod
    def add(self, machine: Machine, snapshot: MachineSnapshot) -> MachineSnapshot: ...

    @abstractmethod
    def latest_for_machine(self, machine_db_id: int) -> MachineSnapshot | None: ...

    @abstractmethod
    def history_for_machine(self, machine_db_id: int, limit: int = 50) -> list[MachineSnapshot]: ...

    @abstractmethod
    def latest_per_machine(self) -> list[MachineSnapshot]: ...

    @abstractmethod
    def snapshots_since(self, since: datetime) -> list[MachineSnapshot]: ...
