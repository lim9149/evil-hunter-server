# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter, HTTPException, Query

from core.cache import SimpleTTLCache
from core.guide_content import STORY_CHAPTERS, BEGINNER_GUIDE_QUESTS, OPTIONAL_AD_UX_RULES
from core.schemas import StoryProgressUpdateRequest, TutorialQuestCompleteRequest
from storage.sqlite_db import complete_tutorial_quest, list_tutorial_progress, upsert_story_progress, get_story_progress, list_active_announcements

router = APIRouter()
_story_cache = SimpleTTLCache(ttl_sec=60)
_quest_cache = SimpleTTLCache(ttl_sec=60)
_ux_cache = SimpleTTLCache(ttl_sec=60)


@router.get('/story/chapters')
def get_story_chapters(accountId: str | None = Query(default=None)):
    progress = get_story_progress(accountId) if accountId else None
    chapters = STORY_CHAPTERS if accountId else _story_cache.get_or_set(lambda: STORY_CHAPTERS)
    return {"workingTitle": "무림객잔: 문파 재건기", "chapters": chapters, "progress": progress, "announcements": list_active_announcements()[:3]}


@router.post('/story/progress')
def post_story_progress(req: StoryProgressUpdateRequest):
    chapter_ids = {chapter["chapterId"] for chapter in STORY_CHAPTERS}
    if req.chapterId not in chapter_ids:
        raise HTTPException(status_code=404, detail="Story chapter not found")
    return upsert_story_progress(req.accountId, req.chapterId)


@router.get('/tutorial/guide-quests')
def get_tutorial_guide_quests(accountId: str | None = Query(default=None)):
    completed = []
    if accountId:
        completed = [row["questId"] for row in list_tutorial_progress(accountId)]
    catalog = BEGINNER_GUIDE_QUESTS if accountId else _quest_cache.get_or_set(lambda: BEGINNER_GUIDE_QUESTS)
    enriched = []
    for quest in catalog:
        item = dict(quest)
        item["completed"] = item["questId"] in completed
        enriched.append(item)
    next_required = next((q["questId"] for q in enriched if (not q["isOptionalAd"]) and (not q["completed"])), None)
    return {"workingTitle": "무림객잔: 문파 재건기", "quests": enriched, "nextRequiredQuestId": next_required}


@router.post('/tutorial/progress/complete')
def post_tutorial_progress_complete(req: TutorialQuestCompleteRequest):
    quest_ids = {quest["questId"] for quest in BEGINNER_GUIDE_QUESTS}
    if req.questId not in quest_ids:
        raise HTTPException(status_code=404, detail="Guide quest not found")
    saved = complete_tutorial_quest(req.accountId, req.questId)
    completed_ids = [row["questId"] for row in list_tutorial_progress(req.accountId)]
    next_required = next((q["questId"] for q in BEGINNER_GUIDE_QUESTS if (not q["isOptionalAd"]) and (q["questId"] not in completed_ids)), None)
    return {"saved": saved, "nextRequiredQuestId": next_required, "completedQuestIds": completed_ids}


@router.get('/tutorial/progress/{account_id}')
def get_tutorial_progress(account_id: str):
    progress = list_tutorial_progress(account_id)
    completed_ids = [row["questId"] for row in progress]
    return {"accountId": account_id, "completedQuestIds": completed_ids, "rows": progress}


@router.get('/ads/ux-rules')
def get_ads_ux_rules():
    return _ux_cache.get_or_set(lambda: OPTIONAL_AD_UX_RULES)


@router.get('/announcements/active')
def get_active_announcements():
    return {"announcements": list_active_announcements()}
