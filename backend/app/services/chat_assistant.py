"""Answers natural-language questions about the fleet by grounding an
IExplanationService in the latest snapshot data — never letting the LLM (or
its rule-based fallback) invent numbers that didn't come from the model."""
from __future__ import annotations

import re

from app.orm.models import MachineSnapshot
from app.repositories.interfaces import IMachineRepository, ISnapshotRepository
from app.services.interfaces import IExplanationService

_MACHINE_ID_PATTERN = re.compile(r"\bM-\d+\b", re.IGNORECASE)


class ChatAssistantService:
    def __init__(
        self,
        machine_repo: IMachineRepository,
        snapshot_repo: ISnapshotRepository,
        explanation_service: IExplanationService,
    ):
        self._machine_repo = machine_repo
        self._snapshot_repo = snapshot_repo
        self._explanation_service = explanation_service

    def ask(self, question: str) -> tuple[str, list[str]]:
        mentioned_ids = [m.upper() for m in _MACHINE_ID_PATTERN.findall(question)]
        latest_snapshots = self._snapshot_repo.latest_per_machine()

        if mentioned_ids:
            relevant = [
                s for s in latest_snapshots if self._machine_id_for(s) in mentioned_ids
            ]
        elif self._is_high_risk_query(question):
            relevant = sorted(latest_snapshots, key=lambda s: s.health_score)[:10]
        else:
            relevant = sorted(latest_snapshots, key=lambda s: s.health_score)[:15]

        context = self._build_context(relevant)
        answer = self._explanation_service.answer_question(question, context)
        referenced = sorted({self._machine_id_for(s) for s in relevant})
        return answer, referenced

    def _machine_id_for(self, snapshot: MachineSnapshot) -> str:
        return snapshot.machine.machine_id

    @staticmethod
    def _is_high_risk_query(question: str) -> bool:
        keywords = ["today", "critical", "urgent", "risk", "maintenance", "need"]
        q = question.lower()
        return any(k in q for k in keywords)

    @staticmethod
    def _build_context(snapshots: list[MachineSnapshot]) -> str:
        if not snapshots:
            return "No machine data available."
        lines = []
        for s in snapshots:
            lines.append(
                f"- {s.machine.machine_id}: health={s.health_score:.0f} "
                f"({s.health_status}), failure_probability={s.failure_probability * 100:.0f}%, "
                f"predicted_failure={s.predicted_failure_type}, priority={s.priority}, "
                f"action='{s.recommended_action}'"
            )
        return "\n".join(lines)
