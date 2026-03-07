from fastapi import APIRouter, HTTPException
from core.schemas import Map
from storage.repo_registry import map_repo as repo

router = APIRouter()

@router.get("")
def list_maps():
    return list(repo.list().values())

@router.get("/{map_id}")
def get_map(map_id: str):
    m = repo.get(map_id)
    if not m:
        raise HTTPException(status_code=404, detail="Map not found")
    return m

@router.post("")
def upsert_map(item: Map):
    return repo.upsert(item)

@router.delete("/{map_id}")
def delete_map(map_id: str):
    ok = repo.delete(map_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Map not found")
    return {"deleted": True}