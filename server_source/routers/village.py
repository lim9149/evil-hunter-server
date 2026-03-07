from fastapi import APIRouter, HTTPException
from core.schemas import Village
from storage.repo_registry import village_repo as repo

router = APIRouter()

@router.get("")
def list_villages():
    return list(repo.list().values())

@router.get("/{village_id}")
def get_village(village_id: str):
    v = repo.get(village_id)
    if not v:
        raise HTTPException(status_code=404, detail="Village not found")
    return v

@router.post("")
def upsert_village(item: Village):
    return repo.upsert(item)

@router.delete("/{village_id}")
def delete_village(village_id: str):
    ok = repo.delete(village_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Village not found")
    return {"deleted": True}