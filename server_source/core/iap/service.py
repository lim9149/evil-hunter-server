import json
import time
from typing import Any, Dict, Optional, Tuple

from core.iap.verifier import allow_stub_verify, verify_apple_signed_jws
from storage.sqlite_db import (
    insert_currency_ledger_idempotent,
    get_conn,
)
from core.audit import write_audit


# -------------------------
# helpers
# -------------------------
def _now_epoch() -> int:
    return int(time.time())


def _get_iap_product_reward(product_id: str) -> Tuple[str, int]:
    """
    Look up product_id -> (currency, amount) from SQLite table iap_products.
    Fallback: gems 100 for backwards compatibility.
    """
    conn = get_conn()
    row = conn.execute(
        "SELECT currency, amount FROM iap_products WHERE product_id=?;",
        (str(product_id),),
    ).fetchone()
    if not row:
        return "gems", 100
    return str(row[0]), int(row[1])


def _upsert_purchase_record(
    provider: str,
    provider_tx_id: str,
    account_id: str,
    product_id: str,
    status: str,
    raw_json: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Insert purchase row (idempotent by unique index uq_purchases_provider_tx).
    """
    conn = get_conn()
    purchase_id = f"pur_{provider}:{provider_tx_id}"
    conn.execute(
        """
        INSERT OR IGNORE INTO purchases(
          purchase_id, provider, provider_tx_id, account_id, product_id, status, raw_json, created_at
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            purchase_id,
            str(provider),
            str(provider_tx_id),
            str(account_id),
            str(product_id),
            str(status),
            None if raw_json is None else json.dumps(raw_json, ensure_ascii=False),
            _now_epoch(),
        ),
    )


def _grant_currency_idempotent(
    account_id: str,
    currency: str,
    amount: int,
    source_kind: str,
    source_id: str,
) -> bool:
    """
    Grants currency via currency_ledger unique(source_kind, source_id).
    Returns True if granted; False if already granted.
    """
    return insert_currency_ledger_idempotent(
        account_id=str(account_id),
        currency=str(currency),
        amount=int(amount),
        source_kind=str(source_kind),
        source_id=str(source_id),
    )


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


# -------------------------
# public service APIs
# -------------------------
def verify_google_purchase_and_grant(
    account_id: str,
    product_id: str,
    purchase_token: str,
    tx_id: str,
    raw: Optional[Dict[str, Any]] = None,
    # Backward-compatible: routers may pass raw_json as string
    raw_json: Optional[str] = None,
) -> Dict[str, Any]:
    ...
    if raw is None and raw_json is not None:
        try:
            raw = json.loads(raw_json)
        except Exception:
            raw = {"raw": raw_json}
    ...
    """
    Google Play purchase verification (currently TODO external verify).
    We still:
      - record purchase row (idempotent)
      - grant reward via currency_ledger idempotency (source_kind='iap_google', source_id=tx_id)
      - write audit log
    """
    provider = "google"
    provider_tx_id = str(tx_id or purchase_token)

    # 1) record purchase (idempotent)
    _upsert_purchase_record(
        provider=provider,
        provider_tx_id=provider_tx_id,
        account_id=account_id,
        product_id=product_id,
        status="verified_stub",
        raw_json=raw or {"purchaseToken": purchase_token, "txId": tx_id},
    )

    # 2) grant by catalog
    currency, amount = _get_iap_product_reward(product_id)

    granted = _grant_currency_idempotent(
        account_id=account_id,
        currency=currency,
        amount=amount,
        source_kind="iap_google",
        source_id=provider_tx_id,
    )

    # 3) audit
    write_audit(
        kind="iap_google_verify",
        actor=str(account_id),
        target=str(provider_tx_id),
        payload={
            "productId": product_id,
            "currency": currency,
            "amount": int(amount),
            "granted": bool(granted),
            "status": "verified_stub",
        },
    )

    return {
        "provider": "google",
        "accountId": str(account_id),
        "productId": str(product_id),
        "txId": str(provider_tx_id),
        "status": "verified_stub",
        "granted": bool(granted),
        "reward": {"currency": currency, "amount": int(amount)},
    }

def verify_apple_purchase_and_grant(
    account_id: str,
    product_id: str,
    tx_id: str,
    raw: Optional[Dict[str, Any]] = None,
    raw_json: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apple purchase verification (currently TODO external verify).
    Same semantics as Google.
    """
    if raw is None and raw_json is not None:
        try:
            raw = json.loads(raw_json)
        except Exception:
            raw = {"raw": raw_json}

    provider = "apple"
    provider_tx_id = str(tx_id)

    # JWS signature verification (if provided)
    verified, status, verify_details = verify_apple_signed_jws(raw or {})
    if (not verified) and (not allow_stub_verify()):
        raise ValueError(f"apple purchase verify failed: {verify_details.get('reason', 'unknown')}")

    _upsert_purchase_record(
        provider=provider,
        provider_tx_id=provider_tx_id,
        account_id=account_id,
        product_id=product_id,
        status=str(status),
        raw_json=(raw or {"txId": tx_id}) | {"_verify": verify_details},
    )

    currency, amount = _get_iap_product_reward(product_id)

    granted = _grant_currency_idempotent(
        account_id=account_id,
        currency=currency,
        amount=amount,
        source_kind="iap_apple",
        source_id=provider_tx_id,
    )

    write_audit(
        kind="iap_apple_verify",
        actor=str(account_id),
        target=str(provider_tx_id),
        payload={
            "productId": product_id,
            "currency": currency,
            "amount": int(amount),
            "granted": bool(granted),
            "status": str(status),
            "verify": verify_details,
        },
    )

    return {
        "provider": "apple",
        "accountId": str(account_id),
        "productId": str(product_id),
        "txId": str(provider_tx_id),
        "status": str(status),
        "granted": bool(granted),
        "reward": {"currency": currency, "amount": int(amount)},
        "verify": verify_details,
    }