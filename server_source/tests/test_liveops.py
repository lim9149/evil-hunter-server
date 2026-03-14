# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_admin_mailbox_grant_and_player_claim_and_announcement_read():
    login = client.post('/admin/auth/login', json={'adminKey': 'dev-admin-key'})
    assert login.status_code == 200
    admin_headers = {'Authorization': f"Bearer {login.json()['adminToken']}"}
    ann = client.post('/admin/tools/announcement/upsert', json={
        'title': '점검 없음',
        'body': '오늘은 정상 운영합니다.',
        'startsAtEpochSec': 1700000000,
        'endsAtEpochSec': 4102444800,
        'priority': 10,
        'isEnabled': True,
    }, headers=admin_headers)
    assert ann.status_code == 200

    res = client.post('/admin/tools/mailbox/grant', json={
        'accountId': 'acc_mail',
        'title': '운영 보상',
        'body': '불편 보상입니다.',
        'rewardCurrency': 'gems',
        'rewardAmount': 50,
    }, headers=admin_headers)
    assert res.status_code == 200

    mailbox = client.get('/player/mailbox/acc_mail')
    assert mailbox.status_code == 200
    messages = mailbox.json()['messages']
    assert len(messages) >= 1
    message_id = messages[0]['messageId']

    claim = client.post(f'/player/mailbox/{message_id}/claim')
    assert claim.status_code == 200
    assert claim.json()['status'] == 'claimed'

    economy = client.get('/player/economy/acc_mail')
    assert economy.status_code == 200
    assert economy.json()['balances']['gems'] >= 50

    announcements = client.get('/player/announcements')
    assert announcements.status_code == 200
    assert len(announcements.json()['announcements']) >= 1


def test_telemetry_batch_ingest():
    res = client.post('/telemetry/events', json={'events': [
        {'accountId': 'acc_tel', 'eventType': 'tutorial', 'eventName': 'guide_complete', 'payload': {'questId': 'guide_001'}},
        {'accountId': 'acc_tel', 'eventType': 'ads', 'eventName': 'offer_opened', 'payload': {'offerId': 'ad_temple_gold_small'}},
    ]})
    assert res.status_code == 200
    payload = res.json()
    assert payload['received'] == 2
    assert payload['inserted'] == 2
