from fastapi import FastAPI
from routers.monster import router as monster_router
from routers.map import router as map_router
from routers.village import router as village_router
from routers.offline import router as offline_router
from routers.worldboss_pvp import router as worldboss_pvp_router
from routers.admin_mode import router as admin_mode_router

app = FastAPI(title="EvilHunterTycoon Server", version="0.1.0")

app.include_router(monster_router, prefix="/monsters", tags=["Monster"])
app.include_router(map_router, prefix="/maps", tags=["Map"])
app.include_router(village_router, prefix="/villages", tags=["Village"])
app.include_router(offline_router, prefix="/offline", tags=["Offline"])
app.include_router(worldboss_pvp_router, tags=["WorldBoss", "PvP"])
app.include_router(admin_mode_router, prefix="/admin", tags=["AdminMode"])

from routers.hunter import router as hunter_router
from routers.combat import router as combat_router

app.include_router(hunter_router, prefix="/hunters", tags=["Hunter"])
app.include_router(combat_router, prefix="/combat", tags=["Combat"])