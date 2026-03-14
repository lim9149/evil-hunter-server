# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_tutorial_progress_roundtrip():
    res = client.get('/tutorial/guide-quests', params={'accountId': 'acc_1'})
    assert res.status_code == 200
    assert res.json()['nextRequiredQuestId'] == 'guide_001'

    save = client.post('/tutorial/progress/complete', json={'accountId': 'acc_1', 'questId': 'guide_001'})
    assert save.status_code == 200
    payload = save.json()
    assert 'guide_001' in payload['completedQuestIds']
    assert payload['nextRequiredQuestId'] == 'guide_002'

    res2 = client.get('/tutorial/guide-quests', params={'accountId': 'acc_1'})
    quests = {q['questId']: q for q in res2.json()['quests']}
    assert quests['guide_001']['completed'] is True


def test_story_progress_saved_and_announcements_surface():
    res = client.post('/story/progress', json={'accountId': 'acc_story', 'chapterId': 'chapter_02_echo_of_blade'})
    assert res.status_code == 200

    fetch = client.get('/story/chapters', params={'accountId': 'acc_story'})
    assert fetch.status_code == 200
    assert fetch.json()['progress']['currentChapterId'] == 'chapter_02_echo_of_blade'
    assert 'announcements' in fetch.json()


def test_ad_claim_requires_complete_step_and_daily_cap():
    offer_res = client.get('/ads/offers', params={'accountId': 'acc_ads'})
    assert offer_res.status_code == 200
    offers = {row['offerId']: row for row in offer_res.json()['offers']}
    assert offers['ad_temple_gold_small']['remainingToday'] == 3

    session = client.post('/ads/session/start', json={
        'accountId': 'acc_ads',
        'offerId': 'ad_temple_gold_small',
        'placement': 'ad_shrine',
    })
    assert session.status_code == 200
    token = session.json()['adViewToken']

    bad = client.post('/ads/reward-claim', json={
        'accountId': 'acc_ads',
        'offerId': 'ad_temple_gold_small',
        'adViewToken': token,
        'completionToken': 'adc_invalid_00',
        'placement': 'ad_shrine',
    })
    assert bad.status_code == 401

    issued = []
    for i in range(3):
        if i > 0:
            session = client.post('/ads/session/start', json={
                'accountId': 'acc_ads',
                'offerId': 'ad_temple_gold_small',
                'placement': 'ad_shrine',
            })
            assert session.status_code == 200
            token = session.json()['adViewToken']
        issued.append(token)
        complete = client.post('/ads/session/complete', json={
            'accountId': 'acc_ads',
            'offerId': 'ad_temple_gold_small',
            'adViewToken': token,
            'placement': 'ad_shrine',
            'adNetwork': 'rewarded',
            'adUnitId': 'temple_gold',
            'completionProof': f'proof_{i}_done',
        })
        assert complete.status_code == 200
        completion_token = complete.json()['completionToken']
        claim = client.post('/ads/reward-claim', json={
            'accountId': 'acc_ads',
            'offerId': 'ad_temple_gold_small',
            'adViewToken': token,
            'completionToken': completion_token,
            'placement': 'ad_shrine',
        })
        assert claim.status_code == 200
        assert claim.json()['status'] == 'claimed'

    dup_complete = client.post('/ads/session/complete', json={
        'accountId': 'acc_ads',
        'offerId': 'ad_temple_gold_small',
        'adViewToken': issued[0],
        'placement': 'ad_shrine',
        'adNetwork': 'rewarded',
        'adUnitId': 'temple_gold',
        'completionProof': 'proof_dup_done',
    })
    assert dup_complete.status_code in (200, 409)

    dup = client.post('/ads/reward-claim', json={
        'accountId': 'acc_ads',
        'offerId': 'ad_temple_gold_small',
        'adViewToken': issued[0],
        'completionToken': 'adc_' + issued[0][-12:],
        'placement': 'ad_shrine',
    })
    assert dup.status_code == 200
    assert dup.json()['status'] == 'duplicate'

    blocked = client.post('/ads/session/start', json={
        'accountId': 'acc_ads',
        'offerId': 'ad_temple_gold_small',
        'placement': 'ad_shrine',
    })
    assert blocked.status_code == 409
