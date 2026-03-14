# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os

from core.auth import service as auth_svc
from core.auth.apple_identity import verify_apple_identity_token
from core.audit import write_audit
from core.security.deps import require_player

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

router = APIRouter()


class GuestLoginReq(BaseModel):
    deviceId: str


class OAuthLoginReq(BaseModel):
    idToken: str
    deviceId: str


class AppleOAuthReq(BaseModel):
    identityToken: str
    deviceId: str


class RefreshReq(BaseModel):
    refreshToken: str
    deviceId: str


class LinkGoogleReq(BaseModel):
    idToken: str


class LinkAppleReq(BaseModel):
    identityToken: str


@router.post("/guest")
def guest_login(req: GuestLoginReq):
    data = auth_svc.guest_login(req.deviceId)
    write_audit("auth_guest", actor=data["accountId"], target=None, payload={"deviceId": req.deviceId})
    return data


@router.post("/refresh")
def refresh(req: RefreshReq):
    try:
        data = auth_svc.rotate_refresh(req.refreshToken, req.deviceId)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    write_audit("auth_refresh", actor=data["accountId"], target=None, payload={"deviceId": req.deviceId})
    return data


@router.post("/logout")
def logout(deviceId: str, account_id: str = Depends(require_player)):
    auth_svc.revoke_device_refreshes(account_id, deviceId)
    write_audit("auth_logout", actor=account_id, target=None, payload={"deviceId": deviceId})
    return {"ok": True}


@router.post("/oauth/google")
def oauth_google(req: OAuthLoginReq):
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    try:
        greq = google_requests.Request()
        if google_client_id:
            info = google_id_token.verify_oauth2_token(req.idToken, greq, google_client_id)
        else:
            info = google_id_token.verify_oauth2_token(req.idToken, greq)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid Google id token")

    provider_sub = info.get("sub")
    if not provider_sub:
        raise HTTPException(status_code=401, detail="invalid Google token payload")

    data = auth_svc.oauth_login("google", provider_sub, req.deviceId)
    write_audit("auth_oauth_google", actor=data["accountId"], target=None, payload={"email": info.get("email")})
    return data


@router.post("/oauth/apple")
def oauth_apple(req: AppleOAuthReq):
    try:
        info = verify_apple_identity_token(req.identityToken)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    data = auth_svc.oauth_login("apple", info["sub"], req.deviceId)
    write_audit("auth_oauth_apple", actor=data["accountId"], target=None, payload={"email": info.get("email"), "verifiedMode": info.get("verifiedMode")})
    return data


@router.post("/link/google")
def link_google(req: LinkGoogleReq, account_id: str = Depends(require_player)):
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    try:
        greq = google_requests.Request()
        if google_client_id:
            info = google_id_token.verify_oauth2_token(req.idToken, greq, google_client_id)
        else:
            info = google_id_token.verify_oauth2_token(req.idToken, greq)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid Google id token")

    provider_sub = info.get("sub")
    if not provider_sub:
        raise HTTPException(status_code=401, detail="invalid Google token payload")

    try:
        auth_svc.link_identity(account_id, "google", provider_sub)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    write_audit("auth_link_google", actor=account_id, target=None, payload={"email": info.get("email")})
    return {"ok": True}


@router.post("/link/apple")
def link_apple(req: LinkAppleReq, account_id: str = Depends(require_player)):
    try:
        info = verify_apple_identity_token(req.identityToken)
        auth_svc.link_identity(account_id, "apple", info["sub"])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    write_audit("auth_link_apple", actor=account_id, target=None, payload={"verifiedMode": info.get("verifiedMode")})
    return {"ok": True}
