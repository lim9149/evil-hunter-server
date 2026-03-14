# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_story_chapters_available():
    response = client.get('/story/chapters')
    assert response.status_code == 200
    data = response.json()
    assert data['workingTitle'] == '무림객잔: 문파 재건기'
    assert len(data['chapters']) >= 4


def test_probability_disclosures_sum_to_100():
    response = client.get('/compliance/probability-disclosures')
    assert response.status_code == 200
    payload = response.json()
    assert payload['disclosures']
    for table in payload['disclosures']:
        total = sum(entry['probabilityPercent'] for entry in table['entries'])
        assert abs(total - 100.0) < 1e-6
