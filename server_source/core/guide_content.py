# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

STORY_CHAPTERS = [
    {
        "chapterId": "prologue_burning_ledgers",
        "title": "프롤로그 - 불타는 장부와 빈 객잔",
        "goal": "폐허가 된 객잔을 조사하고 잔향패를 회수한다.",
        "summary": "문파의 마지막 장부지기인 주인공은 불탄 객잔 지하 금고에서 청심비록과 잔향패를 발견한다. 이 유물은 무기와 방에 남은 잔향을 읽어 과거를 추적하게 해 준다.",
    },
    {
        "chapterId": "chapter_01_first_guest",
        "title": "1장 - 첫 손님, 첫 제자",
        "goal": "떠돌이 무인 1명을 모집하고 객잔 간판을 다시 건다.",
        "summary": "무너진 객잔을 다시 열기 위해 철갑/검객/신궁/도사 중 한 명을 첫 동료로 맞이한다. 플레이어는 사냥-귀환-회복의 핵심 루프를 처음 경험한다.",
    },
    {
        "chapterId": "chapter_02_echo_of_blade",
        "title": "2장 - 칼의 잔향",
        "goal": "사라진 문파 지부의 단서를 확보한다.",
        "summary": "잔향패가 반응한 낡은 검에서 옛 지부의 좌표와 배신자의 흔적이 드러난다. 객잔은 문파 재건 네트워크의 출발점이 된다.",
    },
    {
        "chapterId": "chapter_03_black_market",
        "title": "3장 - 흑시회와 혈야맹",
        "goal": "교역 게시판을 열고 적대 세력의 움직임을 파악한다.",
        "summary": "흑시회와 혈야맹은 봉인 조각이 숨겨진 객잔들을 수색하고 있다. 플레이어는 상단과 협력해 정보망을 넓혀야 한다.",
    },
    {
        "chapterId": "chapter_04_rebuild_banner",
        "title": "4장 - 문파의 깃발",
        "goal": "등봉/화경 헌터를 확보하고 문파 깃발을 세운다.",
        "summary": "전직과 증표 시스템을 통해 각 헌터가 문파의 정체성을 갖추기 시작한다. 작은 객잔은 다시 무림의 거점으로 성장한다.",
    },
    {
        "chapterId": "chapter_05_sealed_peak",
        "title": "5장 - 봉인된 산문",
        "goal": "봉인 조각의 위치를 따라 잃어버린 산문에 도달한다.",
        "summary": "객잔에서 모은 헌터와 상단, 지역 세력의 협력이 완성되며 문파 재건의 첫 번째 진실이 드러난다. 이후 시즌형 확장 스토리의 연결점이 된다.",
    },
]

BEGINNER_GUIDE_QUESTS = [
    {"questId": "guide_001", "title": "객잔 간판 닦기", "description": "객잔 간판을 눌러 상태를 확인하세요.", "category": "village", "isOptionalAd": False},
    {"questId": "guide_002", "title": "첫 헌터 모집", "description": "떠돌이 무인 1명을 객잔에 받아들이세요.", "category": "recruit", "isOptionalAd": False},
    {"questId": "guide_003", "title": "첫 사냥 보내기", "description": "헌터를 사냥터로 출발시키세요.", "category": "hunt", "isOptionalAd": False},
    {"questId": "guide_004", "title": "귀환 확인", "description": "헌터가 허기나 체력 부족으로 마을로 돌아오는 것을 확인하세요.", "category": "loop", "isOptionalAd": False},
    {"questId": "guide_005", "title": "주점 이용", "description": "배고픈 헌터를 주점으로 보내세요.", "category": "facility", "isOptionalAd": False},
    {"questId": "guide_006", "title": "숙소 이용", "description": "지친 헌터를 숙소로 보내세요.", "category": "facility", "isOptionalAd": False},
    {"questId": "guide_007", "title": "의원 이용", "description": "다친 헌터를 의원으로 보내세요.", "category": "facility", "isOptionalAd": False},
    {"questId": "guide_008", "title": "장비 확인", "description": "첫 장비 탭을 열어 보유 장비를 확인하세요.", "category": "gear", "isOptionalAd": False},
    {"questId": "guide_009", "title": "전직 단서 읽기", "description": "증표 설명을 열어 전직 단계를 확인하세요.", "category": "progression", "isOptionalAd": False},
    {"questId": "guide_010", "title": "등봉 도전", "description": "헌터 1명을 등봉 단계까지 육성하세요.", "category": "progression", "isOptionalAd": False},
    {"questId": "guide_011", "title": "객잔 장부 확인", "description": "스토리 패널에서 다음 챕터 목표를 확인하세요.", "category": "story", "isOptionalAd": False},
    {"questId": "guide_012", "title": "교역 게시판 개방", "description": "교역 게시판을 열고 마을 운영 메뉴를 확인하세요.", "category": "village", "isOptionalAd": False},
    {"questId": "guide_013", "title": "광고 신전 안내", "description": "광고 신전 설명을 읽어 보세요. 이 단계는 선택 사항입니다.", "category": "ads", "isOptionalAd": True},
    {"questId": "guide_014", "title": "선택형 광고 1회 체험", "description": "원할 경우 광고 1회를 보고 소량의 골드를 받으세요.", "category": "ads", "isOptionalAd": True},
    {"questId": "guide_015", "title": "확률표기 열람", "description": "확률형 보상 표기 버튼을 눌러 비율을 확인하세요.", "category": "compliance", "isOptionalAd": False},
]

OPTIONAL_AD_UX_RULES = {
    "principles": [
        "광고는 플레이어가 눌렀을 때만 재생한다.",
        "배너/강제 전면/전투 중 자동광고를 사용하지 않는다.",
        "마을 복귀, 일일 보상, 광고 신전 등 자연스러운 구간에서만 버튼을 노출한다.",
        "광고를 보지 않아도 기본 진행은 막히지 않게 설계한다.",
        "보상은 편의·보조 성격으로 유지하고 핵심 전투 승패를 좌우하지 않게 제한한다.",
    ],
    "naturalPlacements": ["광고 신전", "전투 종료 직후 결과창 하단", "일일 목표 보상창", "던전 재도전 확인창"],
}
