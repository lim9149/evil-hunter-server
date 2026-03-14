# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter

from core.cache import SimpleTTLCache
from core.compliance_content import PROBABILITY_DISCLOSURES, LOOTBOX_RULES

router = APIRouter()
_prob_cache = SimpleTTLCache(ttl_sec=120)
_rule_cache = SimpleTTLCache(ttl_sec=120)


@router.get('/compliance/probability-disclosures')
def get_probability_disclosures():
    return {"disclosures": _prob_cache.get_or_set(lambda: PROBABILITY_DISCLOSURES)}


@router.get('/compliance/lootbox-rules')
def get_lootbox_rules():
    return _rule_cache.get_or_set(lambda: LOOTBOX_RULES)
