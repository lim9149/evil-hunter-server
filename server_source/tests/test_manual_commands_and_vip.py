from fastapi.testclient import TestClient

from main import app
from storage.repo_registry import hunter_repo


client = TestClient(app)


def setup_function():
    hunter_repo.items.clear()


def test_hunter_manual_command_roundtrip():
    payload = {
        "hunterId": "h_cmd",
        "accountId": "acc1",
        "slotIndex": 0,
        "name": "명령헌터",
        "jobId": "novice",
        "level": 1,
        "hp": 100,
        "atk": 10,
        "defense": 5,
        "powerScore": 25,
    }
    r = client.post('/hunters', json=payload)
    assert r.status_code == 200

    r = client.post('/hunters/h_cmd/command', json={"command": "hunt", "desiredMonsterCount": 5})
    assert r.status_code == 200
    body = r.json()
    assert body['command'] == 'hunt'
    assert body['desiredMonsterCount'] == 5

    r = client.get('/hunters/h_cmd')
    assert r.status_code == 200
    hunter = r.json()
    assert hunter['activeCommand'] == 'hunt'
    assert hunter['desiredMonsterCount'] == 5
    assert hunter['manualControl'] is True


def test_ads_vip_status_defaults_to_zero():
    r = client.get('/ads/vip-status', params={'accountId': 'acc1'})
    assert r.status_code == 200
    body = r.json()
    assert body['vipLevel'] == 0
    assert body['nextVipLevel'] == 1
