from fastapi import APIRouter, HTTPException
from core.schemas import CombatFightRequest, CombatFightResponse
from core.combat import fight_time_to_kill
from storage.repo_registry import hunter_repo as hunters, monster_repo as monsters

router = APIRouter()

@router.post("/fight", response_model=CombatFightResponse)
def fight(req: CombatFightRequest):
    # 같은 공용 상자에서 hunter/monster를 읽는다!
    h = hunters.get(req.hunterId)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    m = monsters.get(req.monsterId)
    if not m:
        raise HTTPException(status_code=404, detail="Monster not found")

    atk_mul = float(req.buffs.get("atkMul", 1.0))

    result = fight_time_to_kill(
        hunter_atk=h.atk,
        monster_def=m.defense,
        monster_hp=m.hp,
        atk_mul=atk_mul,
    )

    return CombatFightResponse(
        hunterId=req.hunterId,
        monsterId=req.monsterId,
        damagePerHit=result["damagePerHit"],
        hitsToKill=result["hitsToKill"],
        totalSec=result["totalSec"],
        fightSucceed=result["fightSucceed"],
        breakdown=result["breakdown"],
    )