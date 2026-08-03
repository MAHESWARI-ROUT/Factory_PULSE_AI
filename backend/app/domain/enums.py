"""Domain-level enumerations. These are the vocabulary of the business, kept
free of any framework or persistence concerns so they can be imported by
schemas, services, and the ORM layer alike without creating import cycles."""
from __future__ import annotations

from enum import Enum


class MachineType(str, Enum):
    LOW = "L"
    MEDIUM = "M"
    HIGH = "H"


class FailureType(str, Enum):
    NONE = "NONE"
    HEAT_DISSIPATION_FAILURE = "HDF"
    POWER_FAILURE = "PWF"
    OVERSTRAIN_FAILURE = "OSF"
    TOOL_WEAR_FAILURE = "TWF"
    RANDOM_FAILURE = "RNF"

    @property
    def display_name(self) -> str:
        return _FAILURE_TYPE_LABELS.get(self, self.value)


_FAILURE_TYPE_LABELS = {
    FailureType.NONE: "No Failure Detected",
    FailureType.HEAT_DISSIPATION_FAILURE: "Heat Dissipation Failure",
    FailureType.POWER_FAILURE: "Power Failure",
    FailureType.OVERSTRAIN_FAILURE: "Overstrain Failure",
    FailureType.TOOL_WEAR_FAILURE: "Tool Wear Failure",
    FailureType.RANDOM_FAILURE: "Random Failure",
}


class HealthStatus(str, Enum):
    EXCELLENT = "Excellent"
    HEALTHY = "Healthy"
    WARNING = "Warning"
    CRITICAL = "Critical"


class MaintenancePriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"
