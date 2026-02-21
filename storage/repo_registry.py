from storage.memory_repo import MemoryRepo
from core.schemas import Monster, Map, Village, Hunter, WorldBoss, PvPSeason

# "공용 상자"들: 이 파일의 repo를 import해서 모두가 똑같은 데이터를 봅니다.
monster_repo = MemoryRepo[Monster](key_field="monsterId")
map_repo = MemoryRepo[Map](key_field="mapId")
village_repo = MemoryRepo[Village](key_field="villageId")
hunter_repo = MemoryRepo[Hunter](key_field="hunterId")
worldboss_repo = MemoryRepo[WorldBoss](key_field="bossId")
pvp_season_repo = MemoryRepo[PvPSeason](key_field="seasonId")