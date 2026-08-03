"""Dev/ops utility endpoints — not part of the core product surface, kept
separate so they can be excluded or protected behind auth in production."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends

from app.api.deps import get_seeder_service
from app.services.data_seeder import DataSeederService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed")
def seed_database(seeder: DataSeederService = Depends(get_seeder_service)) -> dict:
    csv_path = Path("data/ai4i2020.csv")
    inserted = seeder.seed_from_csv(csv_path)
    return {"inserted_snapshots": inserted}
