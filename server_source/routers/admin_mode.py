from fastapi import APIRouter

from core.schemas import AdminModeUpsertRequest
from storage.sqlite_db import upsert_admin_mode, list_admin_modes, get_admin_mode

router = APIRouter()


@router.get("/modes")
def list_modes():
    return list_admin_modes()


@router.get("/modes/{key}")
def get_mode(key: str):
    row = get_admin_mode(key)
    return row or {"key": key, "enabled": False, "multiplier": 1.0}


@router.post("/modes")
def upsert_mode(req: AdminModeUpsertRequest):
    return upsert_admin_mode(req.key, req.enabled, req.multiplier)