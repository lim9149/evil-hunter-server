from storage.repo_registry import monster_repo as repo
from fastapi import APIRouter, HTTPException
from core.schemas import Monster

router = APIRouter()

@router.get("")
def list_monsters():
    return list(repo.list().values())

@router.get("/{monster_id}")
def get_monster(monster_id: str):
    m = repo.get(monster_id)
    if not m:
        raise HTTPException(status_code=404, detail="Monster not found")
    return m

@router.post("")
def upsert_monster(monster: Monster):
    return repo.upsert(monster)

@router.delete("/{monster_id}")
def delete_monster(monster_id: str):
    ok = repo.delete(monster_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Monster not found")
    return {"deleted": True}