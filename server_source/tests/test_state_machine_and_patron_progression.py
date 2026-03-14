from fastapi.testclient import TestClient

from main import app
from storage.repo_registry import hunter_repo
from storage.sqlite_db import insert_ad_claim

client = TestClient(app)


def setup_function():
    hunter_repo.items.clear()


def test_hunter_state_machine_emergency_return_when_low_hp():
    payload = {
        "hunterId": "h_sm_1",
        "accountId": "acc_sm",
        "slotIndex": 0,
        "name": "상태헌터",
        "jobId": "novice",
        "level": 8,
        "hp": 24,
        "atk": 11,
        "defense": 5,
        "powerScore": 40,
        "assignedHuntZoneId": "east_forest",
        "fatigue": 20,
        "satiety": 60,
        "stamina": 18,
    }
    r = client.post('/hunters', json=payload)
    assert r.status_code == 200

    r = client.get('/hunters/h_sm_1/state-machine')
    assert r.status_code == 200
    body = r.json()
    assert body['currentState'] == 'NeedCheck'
    assert body['nextState'] == 'EmergencyReturn'
    assert body['targetLocation'] == 'clinic_or_inn'
    assert 'critical_recovery' in body['riskFlags']


def test_assign_hunt_zone_updates_hunter_and_state_machine():
    payload = {
        "hunterId": "h_sm_2",
        "accountId": "acc_sm",
        "slotIndex": 1,
        "name": "배정헌터",
        "jobId": "novice",
        "level": 10,
        "hp": 100,
        "atk": 14,
        "defense": 7,
        "powerScore": 55,
    }
    assert client.post('/hunters', json=payload).status_code == 200

    r = client.post('/hunters/h_sm_2/assign-hunt-zone', json={"huntZoneId": "north_ridge", "desiredLoopCount": 4})
    assert r.status_code == 200
    body = r.json()
    assert body['huntZoneId'] == 'north_ridge'
    assert body['desiredLoopCount'] == 4

    r = client.get('/hunters/h_sm_2/state-machine')
    assert r.status_code == 200
    sm = r.json()
    assert sm['assignedHuntZoneId'] == 'north_ridge'
    assert sm['targetLocation'] == 'north_ridge'


def test_vip_status_uses_lifetime_claims_and_returns_preview():
    account_id = 'acc_patron'
    for idx in range(21):
        insert_ad_claim(account_id, 'ad_temple_gold_small', f'tok_{idx}', f'2026-03-{(idx % 5) + 1:02d}', 'gold', 100)

    r = client.get('/ads/vip-status', params={'accountId': account_id})
    assert r.status_code == 200
    body = r.json()
    assert body['adViewsLifetime'] == 21
    assert body['vipLevel'] >= 3
    assert body['vipTitle']
    assert isinstance(body['milestonePreview'], list)
    assert 'designIntent' in body
