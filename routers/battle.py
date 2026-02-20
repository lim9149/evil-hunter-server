from fastapi import APIRouter
from core.combat import calculate_damage

router = APIRouter()

@router.post("/battle")
def battle(player_attack: int, monster_hp: int):
    damage = calculate_damage(player_attack)
    monster_hp -= damage
    return {"remaining_hp": monster_hp}