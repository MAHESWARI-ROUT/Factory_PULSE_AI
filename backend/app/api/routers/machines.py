from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_machine_repository, get_snapshot_repository
from app.repositories.interfaces import IMachineRepository, ISnapshotRepository
from app.schemas.machine import MachineDetailOut, MachineListResponse, MachineOut, SnapshotOut

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("", response_model=MachineListResponse)
def list_machines(
    machine_repo: IMachineRepository = Depends(get_machine_repository),
    snapshot_repo: ISnapshotRepository = Depends(get_snapshot_repository),
) -> MachineListResponse:
    machines = machine_repo.list_all()
    out = []
    for m in machines:
        latest = snapshot_repo.latest_for_machine(m.id)
        out.append(
            MachineOut(
                machine_id=m.machine_id,
                machine_type=m.machine_type,
                location=m.location,
                latest_snapshot=SnapshotOut.model_validate(latest) if latest else None,
            )
        )
    return MachineListResponse(total=len(out), machines=out)


@router.get("/{machine_id}", response_model=MachineDetailOut)
def get_machine_detail(
    machine_id: str,
    machine_repo: IMachineRepository = Depends(get_machine_repository),
    snapshot_repo: ISnapshotRepository = Depends(get_snapshot_repository),
) -> MachineDetailOut:
    machine = machine_repo.get_by_machine_id(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")

    history = snapshot_repo.history_for_machine(machine.id, limit=100)
    latest = history[0] if history else None

    return MachineDetailOut(
        machine_id=machine.machine_id,
        machine_type=machine.machine_type,
        location=machine.location,
        latest_snapshot=SnapshotOut.model_validate(latest) if latest else None,
        history=[SnapshotOut.model_validate(s) for s in history],
    )
