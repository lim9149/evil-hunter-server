from fastapi import FastAPI

from core.schemas import HealthResponse

from routers.auth import router as auth_router
from routers.iap import router as iap_router

from routers.monster import router as monster_router
from routers.map import router as map_router
from routers.village import router as village_router
from routers.offline import router as offline_router

from routers.hunter import router as hunter_router
from routers.combat import router as combat_router

from routers.worldboss_pvp import router as worldboss_pvp_router
from routers.admin_mode import router as admin_mode_router

from routers.admin_auth import router as admin_auth_router
from routers.admin_audit import router as admin_audit_router
from routers.admin_tools import router as admin_tools_router
from routers.admin_catalog import router as admin_catalog_router


app = FastAPI(title="EvilHunterTycoon Server", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health():
    """서비스 상태 및 버전. 배포/로드밸런서 헬스체크용."""
    return HealthResponse(ok=True, service="evil-hunter-server", version="0.1.0")


# Core gameplay CRUD
app.include_router(monster_router, prefix="/monsters", tags=["Monster"])
app.include_router(map_router, prefix="/maps", tags=["Map"])
app.include_router(village_router, prefix="/villages", tags=["Village"])
app.include_router(hunter_router, prefix="/hunters", tags=["Hunter"])

# Offline / Combat
app.include_router(offline_router, prefix="/offline", tags=["Offline"])
app.include_router(combat_router, prefix="/combat", tags=["Combat"])

# WorldBoss / PvP (includes reward tier APIs)
app.include_router(worldboss_pvp_router, tags=["WorldBoss", "PvP"])

# Operator(Admin) gameplay tuning (kept open for internal test flows)
app.include_router(admin_mode_router, prefix="/admin", tags=["AdminMode"])

# Player Auth & IAP
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(iap_router, prefix="/iap", tags=["IAP"])

# Admin Auth / Tools / Audit (protected with admin access token)
app.include_router(admin_auth_router, prefix="/admin/auth", tags=["AdminAuth"])
app.include_router(admin_tools_router, prefix="/admin/tools", tags=["AdminTools"])
app.include_router(admin_audit_router, prefix="/admin/audit", tags=["AdminAudit"])

# Admin catalog (tiers/mbti/items/promotion/iap-products)
app.include_router(admin_catalog_router, prefix="/admin/catalog", tags=["AdminCatalog"])