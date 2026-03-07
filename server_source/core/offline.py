from dataclasses import dataclass
from typing import Dict, Any
import math

@dataclass(frozen=True)
class OfflineConfig:
    max_offline_seconds: int = 28800  # 8시간 (밸런스 수치 시트)
    min_grant_seconds: int = 60       # 1분
    gold_per_sec_coeff: float = 0.12  # goldPerSec = sqrt(powerScore)*coeff
    exp_per_sec_coeff: float = 0.05   # expPerSec  = sqrt(powerScore)*coeff

def offline_reward_by_powerscore(
    *,
    last_active_epoch: int,
    now_epoch: int,
    power_score: float,
    map_multiplier: float = 1.2,
    village_gold_buff: float = 0.10,
    village_exp_buff: float = 0.05,
    village_tax_rate: float = 0.0,
    village_storage_bonus: float = 0.0,
    vip_multiplier: float = 1.0,
    event_multiplier: float = 1.0,
    admin_multiplier: float = 1.0,
    config: OfflineConfig = OfflineConfig(),
) -> Dict[str, Any]:
    if now_epoch <= last_active_epoch:
        return {"offlineSeconds": 0, "cappedSeconds": 0, "gold": 0, "exp": 0, "breakdown": {"reason": "now<=last"}}

    offline_seconds = int(now_epoch - last_active_epoch)
    if offline_seconds < config.min_grant_seconds:
        return {"offlineSeconds": offline_seconds, "cappedSeconds": 0, "gold": 0, "exp": 0, "breakdown": {"reason": "below_min"}}

    cap_sec = int(math.floor(config.max_offline_seconds * (1.0 + max(village_storage_bonus, 0.0))))
    capped_sec = min(offline_seconds, cap_sec)

    ps = max(power_score, 0.0)
    base_gold_per_sec = math.sqrt(ps) * config.gold_per_sec_coeff
    base_exp_per_sec  = math.sqrt(ps) * config.exp_per_sec_coeff

    village_gold_mul = 1.0 + max(village_gold_buff, 0.0)
    village_exp_mul  = 1.0 + max(village_exp_buff, 0.0)

    gross_mul = map_multiplier * vip_multiplier * event_multiplier * admin_multiplier

    gross_gold = base_gold_per_sec * capped_sec * gross_mul * village_gold_mul
    gross_exp  = base_exp_per_sec  * capped_sec * gross_mul * village_exp_mul

    tax = min(max(village_tax_rate, 0.0), 1.0)
    net_gold = gross_gold * (1.0 - tax)
    net_exp  = gross_exp  * (1.0 - tax)

    return {
        "offlineSeconds": offline_seconds,
        "cappedSeconds": capped_sec,
        "gold": int(math.floor(net_gold)),
        "exp": int(math.floor(net_exp)),
        "breakdown": {
            "capSeconds": cap_sec,
            "powerScore": ps,
            "baseGoldPerSec": base_gold_per_sec,
            "baseExpPerSec": base_exp_per_sec,
            "mapMultiplier": map_multiplier,
            "vipMultiplier": vip_multiplier,
            "eventMultiplier": event_multiplier,
            "adminMultiplier": admin_multiplier,
            "villageGoldBuff": village_gold_buff,
            "villageExpBuff": village_exp_buff,
            "villageTaxRate": tax,
            "grossMultiplier": gross_mul,
        }
    }


def offline_reward(
    *,
    last_active_epoch: int,
    now_epoch: int,
    base_gold_per_min: float,
    base_exp_per_min: float,
    map_multiplier: float = 1.0,
    village_tax_rate: float = 0.0,
    village_storage_bonus: float = 0.0,
    vip_multiplier: float = 1.0,
    event_multiplier: float = 1.0,
    admin_multiplier: float = 1.0,
    config: OfflineConfig = OfflineConfig(),
) -> Dict[str, Any]:
    """MVP offline reward calculator (rate-based).

    This is the version used by current /offline/preview and /offline/collect APIs and tests.
    """

    if now_epoch <= last_active_epoch:
        return {
            "offlineMinutes": 0,
            "cappedMinutes": 0,
            "gold": 0,
            "exp": 0,
            "breakdown": {"reason": "now<=last"},
        }

    offline_seconds = int(now_epoch - last_active_epoch)
    if offline_seconds < config.min_grant_seconds:
        return {
            "offlineMinutes": offline_seconds // 60,
            "cappedMinutes": 0,
            "gold": 0,
            "exp": 0,
            "breakdown": {"reason": "below_min"},
        }

    cap_sec = int(math.floor(config.max_offline_seconds * (1.0 + max(village_storage_bonus, 0.0))))
    capped_sec = min(offline_seconds, cap_sec)

    offline_minutes = offline_seconds // 60
    capped_minutes = capped_sec // 60

    gross_mul = map_multiplier * vip_multiplier * event_multiplier * admin_multiplier

    gross_gold = float(base_gold_per_min) * capped_minutes * gross_mul
    gross_exp = float(base_exp_per_min) * capped_minutes * gross_mul

    tax = min(max(village_tax_rate, 0.0), 1.0)
    net_gold = gross_gold * (1.0 - tax)
    net_exp = gross_exp * (1.0 - tax)

    return {
        "offlineMinutes": int(offline_minutes),
        "cappedMinutes": int(capped_minutes),
        "gold": int(math.floor(net_gold)),
        "exp": int(math.floor(net_exp)),
        "breakdown": {
            "offlineSeconds": offline_seconds,
            "capSeconds": cap_sec,
            "mapMultiplier": map_multiplier,
            "vipMultiplier": vip_multiplier,
            "eventMultiplier": event_multiplier,
            "adminMultiplier": admin_multiplier,
            "villageTaxRate": tax,
            "grossMultiplier": gross_mul,
            "baseGoldPerMin": float(base_gold_per_min),
            "baseExpPerMin": float(base_exp_per_min),
        },
    }