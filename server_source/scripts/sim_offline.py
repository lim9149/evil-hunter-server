import time
from core.offline import offline_reward

if __name__ == "__main__":
    now = int(time.time())
    # 예: 6시간 오프라인
    last = now - (6 * 60 * 60)

    # 밸런스(시트 '재화_과금_이벤트' / '밸런스 수치'에서 가져올 값이라고 가정)
    base_gold_per_min = 10.0
    base_exp_per_min = 5.0

    r = offline_reward(
        last_active_epoch=last,
        now_epoch=now,
        base_gold_per_min=base_gold_per_min,
        base_exp_per_min=base_exp_per_min,
        map_multiplier=1.2,
        village_tax_rate=0.05,
        village_storage_bonus=0.25,
        vip_multiplier=1.5,
        event_multiplier=2.0,
        admin_multiplier=1.0,
    )
    print("OFFLINE SIM RESULT")
    print(r)