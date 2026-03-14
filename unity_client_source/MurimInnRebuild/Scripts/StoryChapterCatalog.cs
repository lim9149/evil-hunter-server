// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    [System.Serializable]
    public sealed class StoryChapterData
    {
        public string chapterId;
        public string title;
        [TextArea(2, 4)] public string goal;
        [TextArea(3, 6)] public string summary;
    }

    [CreateAssetMenu(fileName = "StoryChapterCatalog", menuName = "MurimInnRebuild/Story Chapter Catalog")]
    public sealed class StoryChapterCatalogSO : ScriptableObject
    {
        public List<StoryChapterData> chapters = new List<StoryChapterData>();

        public static StoryChapterCatalogSO CreateRuntimeDefault()
        {
            StoryChapterCatalogSO catalog = CreateInstance<StoryChapterCatalogSO>();
            catalog.chapters = new List<StoryChapterData>
            {
                new StoryChapterData { chapterId = "prologue_burning_ledgers", title = "프롤로그 - 불타는 장부와 빈 객잔", goal = "잔향패를 회수하고 객잔의 비밀을 연다.", summary = "주인공은 불타버린 객잔 지하에서 청심비록과 잔향패를 발견한다. 이 힘으로 과거 사건의 흔적을 읽어 문파 몰락의 진실을 좇는다." },
                new StoryChapterData { chapterId = "chapter_01_first_guest", title = "1장 - 첫 손님, 첫 제자", goal = "첫 헌터를 영입해 객잔을 다시 연다.", summary = "플레이어는 첫 헌터를 모집하고 사냥과 귀환, 회복의 핵심 루프를 체험한다." },
                new StoryChapterData { chapterId = "chapter_02_echo_of_blade", title = "2장 - 칼의 잔향", goal = "사라진 지부의 좌표를 추적한다.", summary = "낡은 검이 숨겨진 지부와 배신자의 단서를 드러낸다." },
                new StoryChapterData { chapterId = "chapter_03_black_market", title = "3장 - 흑시회와 혈야맹", goal = "교역 게시판을 열고 적대 세력의 움직임을 파악한다.", summary = "객잔은 정보와 사람을 모으는 작은 거점에서 무림 세력전의 중심으로 성장하기 시작한다." },
            };
            return catalog;
        }
    }
}
