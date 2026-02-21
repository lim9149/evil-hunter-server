from storage.repo_registry import hunter_repo as repo
from fastapi import APIRouter, HTTPException, Query
from core.schemas import Hunter

router = APIRouter()

@router.get("")
def list_hunters(accountId: str | None = Query(default=None)):
    items = list(repo.list().values())
    if accountId:
        items = [h for h in items if h.accountId == accountId]
    return items

@router.get("/{hunter_id}")
def get_hunter(hunter_id: str):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    return h

@router.post("")
def upsert_hunter(hunter: Hunter):
    # 계정 내 slotIndex 중복 방지(기본 정책)
    # 같은 accountId + slotIndex에 다른 hunterId가 이미 있으면 에러
    for existing in repo.list().values():
        if existing.accountId == hunter.accountId and existing.slotIndex == hunter.slotIndex:
            if existing.hunterId != hunter.hunterId:
                raise HTTPException(status_code=409, detail="Slot already occupied for this accountId")
    return repo.upsert(hunter)

@router.delete("/{hunter_id}")
def delete_hunter(hunter_id: str):
    ok = repo.delete(hunter_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Hunter not found")
    return {"deleted": True}