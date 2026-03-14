# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.security.jwt import create_admin_token

router = APIRouter()

ADMIN_MASTER_KEY = os.getenv("ADMIN_MASTER_KEY", "dev-admin-key")

class AdminLoginReq(BaseModel):
    adminKey: str

@router.post("/login")
def admin_login(req: AdminLoginReq):
    if req.adminKey != ADMIN_MASTER_KEY:
        raise HTTPException(status_code=403, detail="invalid admin key")

    token = create_admin_token("master_admin", scope="admin")
    return {"adminToken": token}