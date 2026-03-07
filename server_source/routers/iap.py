import json
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from core.security.deps import require_player
from core.security.rate_limit import hit_rate_limit
from core.security.replay_guard import verify_replay_guard
from core.iap.service import verify_google_purchase_and_grant, verify_apple_purchase_and_grant

router = APIRouter()

class GoogleVerifyReq(BaseModel):
    productId: str
    purchaseToken: str
    txId: str
    raw: dict = Field(default_factory=dict)

class AppleVerifyReq(BaseModel):
    productId: str
    txId: str
    raw: dict = Field(default_factory=dict)

def _security_guard(account_id: str, x_req_ts: int | None, x_req_nonce: str | None):
    if not hit_rate_limit(f"iap:{account_id}", limit=10, window_sec=60):
        raise HTTPException(status_code=429, detail="rate limited")
    if x_req_ts is not None and x_req_nonce is not None:
        try:
            verify_replay_guard(account_id, int(x_req_ts), str(x_req_nonce))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/google/verify")
def verify_google(
    req: GoogleVerifyReq,
    account_id: str = Depends(require_player),
    x_req_ts: int | None = Header(default=None, alias="X-Req-TS"),
    x_req_nonce: str | None = Header(default=None, alias="X-Req-Nonce"),
):
    _security_guard(account_id, x_req_ts, x_req_nonce)
    try:
        return verify_google_purchase_and_grant(
            account_id=account_id,
            product_id=req.productId,
            purchase_token=req.purchaseToken,
            tx_id=req.txId,
            raw_json=json.dumps(req.raw, ensure_ascii=False),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/apple/verify")
def verify_apple(
    req: AppleVerifyReq,
    account_id: str = Depends(require_player),
    x_req_ts: int | None = Header(default=None, alias="X-Req-TS"),
    x_req_nonce: str | None = Header(default=None, alias="X-Req-Nonce"),
):
    _security_guard(account_id, x_req_ts, x_req_nonce)
    try:
        return verify_apple_purchase_and_grant(
            account_id=account_id,
            product_id=req.productId,
            tx_id=req.txId,
            raw_json=json.dumps(req.raw, ensure_ascii=False),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))