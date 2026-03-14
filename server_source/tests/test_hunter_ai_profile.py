from fastapi.testclient import TestClient

from main import app
from storage.repo_registry import hunter_repo


client = TestClient(app)


def setup_function():
    hunter_repo.items.clear()


def _seed_hunter():
    payload = {
        "hunterId": "h_ai",
        "accountId": "acc1",
        "slotIndex": 0,
        "name": "자율헌터",
        "jobId": "novice",
        "level": 1,
        "hp": 100,
        "atk": 10,
        "defense": 5,
        "powerScore": 25,
    }
    r = client.post('/hunters', json=payload)
    assert r.status_code == 200


def test_hunter_ai_profile_defaults_to_autonomous():
    _seed_hunter()
    r = client.get('/hunters/h_ai/ai-profile')
    assert r.status_code == 200
    body = r.json()
    assert body['aiMode'] == 'autonomous'
    assert body['preferredActivity'] == 'hunt'
    assert 'Direct orders temporarily override' in ' '.join(body['commandPolicy'])


def test_hunter_ai_profile_can_be_configured():
    _seed_hunter()
    r = client.post('/hunters/h_ai/configure-ai', json={
        'aiMode': 'assisted',
        'preferredActivity': 'train',
        'socialDrive': 72,
        'disciplineDrive': 81,
        'braveryDrive': 33,
    })
    assert r.status_code == 200
    body = r.json()
    assert body['aiMode'] == 'assisted'
    assert body['preferredActivity'] == 'train'
    assert body['socialDrive'] == 72
    assert body['disciplineDrive'] == 81
    assert body['braveryDrive'] == 33
