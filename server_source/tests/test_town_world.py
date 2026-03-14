# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_version_and_service_name():
    res = client.get('/health')
    assert res.status_code == 200
    payload = res.json()
    assert payload['service'] == 'murim-inn-rebuild-server'
    assert payload['version'] == '0.5.0'


def test_town_world_definition_and_snapshot():
    definition = client.get('/world/definition')
    assert definition.status_code == 200
    body = definition.json()
    assert body['sceneName'] == 'TownWorldScene'
    assert body['hudRules']['battleSceneAllowed'] is False
    assert len(body['facilities']) >= 5
    assert len(body['monsterZones']) >= 1

    snap = client.get('/world/snapshot', params={'accountId': 'acc_world'})
    assert snap.status_code == 200
    snap_json = snap.json()
    assert snap_json['accountId'] == 'acc_world'
    assert 'hunt_monsters' in snap_json['recommendedFlow']
