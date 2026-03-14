from fastapi.testclient import TestClient

from main import app
from storage.repo_registry import hunter_repo


client = TestClient(app)


def setup_function():
    hunter_repo.items.clear()


def _hunter(hunter_id: str = "mission_h1", account_id: str = "acc_mission", **extra):
    payload = {
        "hunterId": hunter_id,
        "accountId": account_id,
        "slotIndex": 0,
        "name": "장문운영 테스트",
        "jobId": "novice",
        "level": 40,
        "exp": 0,
        "powerScore": 120,
        "hp": 100,
        "atk": 20,
        "defense": 8,
        "gold": 1200,
        "loyalty": 82,
        "stamina": 85,
        "satiety": 85,
        "insight": 50,
        "sectTokenCount": 2,
        "sectDiscipline": 60,
    }
    payload.update(extra)
    assert client.post('/hunters', json=payload).status_code == 200


def test_operator_mission_progress_and_claim():
    _hunter()
    for _ in range(3):
        r = client.post('/hunters/mission_h1/settle-return', json={
            'foundGold': 800, 'foundMaterials': {'herb': 5}, 'taxRate': 0.1, 'loopsCompleted': 2, 'fatigueDelta': 6, 'satietyDelta': -8, 'durabilityDelta': -4
        })
        assert r.status_code == 200
    snap = client.get('/world/operator/missions', params={'accountId': 'acc_mission'})
    assert snap.status_code == 200
    body = snap.json()
    target = next(m for m in body['missions'] if m['missionId'] == 'daily_settle_3')
    assert target['completed'] is True
    claim = client.post('/world/operator/missions/claim', json={'accountId': 'acc_mission', 'missionId': 'daily_settle_3', 'scope': 'daily'})
    assert claim.status_code == 200
    assert claim.json()['resultCode'] == 'OK_MISSION_CLAIMED'
    claim2 = client.post('/world/operator/missions/claim', json={'accountId': 'acc_mission', 'missionId': 'daily_settle_3', 'scope': 'daily'})
    assert claim2.json()['ok'] is False


def test_growth_rules_and_reforge_require_tokens_and_discipline():
    _hunter('mission_h2', sectTokenCount=0, sectDiscipline=20, bodyReforgeStage=1)
    growth = client.get('/hunters/mission_h2/growth-rules')
    assert growth.status_code == 200
    gbody = growth.json()['bodyReforge']
    assert gbody['hasEnoughSectToken'] is False
    fail = client.post('/hunters/mission_h2/body-reforge', json={'consumeGold': 100, 'consumeMaterials': {'rebirth_pill': 1}})
    assert fail.status_code == 200
    assert fail.json()['resultCode'] in {'ERR_NOT_ENOUGH_SECT_TOKEN', 'ERR_DISCIPLINE_TOO_LOW'}

    client.post('/hunters', json={
        'hunterId': 'mission_h2', 'accountId': 'acc_mission', 'slotIndex': 0, 'name': '장문운영 테스트', 'jobId': 'novice',
        'level': 40, 'exp': 0, 'powerScore': 120, 'hp': 100, 'atk': 20, 'defense': 8, 'gold': 1200, 'loyalty': 82, 'stamina': 85, 'satiety': 85, 'insight': 50,
        'sectTokenCount': 2, 'sectDiscipline': 60, 'bodyReforgeStage': 1
    })
    ok = client.post('/hunters/mission_h2/body-reforge', json={'consumeGold': 100, 'consumeMaterials': {'rebirth_pill': 1}})
    assert ok.status_code == 200
    assert ok.json()['resultCode'] == 'OK_REFORGED'


def test_recipe_catalog_exposes_midgame_unlocks():
    res = client.get('/world/operator/recipes')
    assert res.status_code == 200
    recipes = {r['recipeId']: r for r in res.json()['recipes']}
    assert 'weapon_refined' in recipes
    assert recipes['weapon_refined']['unlockRank'] >= 4
