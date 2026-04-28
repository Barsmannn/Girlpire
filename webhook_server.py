import hashlib
import hmac
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

APP_DIR = Path(__file__).resolve().parent
DATA_PATH = Path(os.getenv("WEBHOOK_DATA_PATH", str(APP_DIR / "emails.json")))
LEMON_WEBHOOK_SECRET = os.getenv("LEMON_WEBHOOK_SECRET", "")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
WEBHOOK_SYNC_SECRET = os.getenv("WEBHOOK_SYNC_SECRET", "")


def ensure_file():
    if not DATA_PATH.exists():
        DATA_PATH.write_text(
            json.dumps({"users": [], "paid_users": [], "vip_memberships": {}}, indent=2) + "\n",
            encoding="utf-8",
        )


def normalize_vip_memberships(items: object) -> dict[str, dict[str, str]]:
    if not isinstance(items, dict):
        return {}

    normalized: dict[str, dict[str, str]] = {}
    for email, raw_value in items.items():
        normalized_email = normalize_email(email)
        if not normalized_email:
            continue

        started_at = ""
        expires_at = ""
        if isinstance(raw_value, dict):
            started_at = str(raw_value.get("started_at", "")).strip()
            expires_at = str(raw_value.get("expires_at", "")).strip()

        if not started_at:
            started_at = datetime_now_date_iso()
        if not expires_at:
            expires_at = add_days_iso(started_at, 30)

        normalized[normalized_email] = {
            "started_at": started_at,
            "expires_at": expires_at,
        }
    return normalized


def datetime_now_date_iso() -> str:
    from datetime import datetime

    return datetime.now().date().isoformat()


def add_days_iso(started_at: str, days: int) -> str:
    from datetime import datetime, timedelta

    try:
        started_date = datetime.fromisoformat(started_at).date()
    except ValueError:
        started_date = datetime.now().date()
    return (started_date + timedelta(days=days)).isoformat()


def read_store() -> dict[str, object]:
    ensure_file()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return {
        "users": data.get("users", []),
        "paid_users": [normalize_email(item) for item in data.get("paid_users", []) if normalize_email(item)],
        "vip_memberships": normalize_vip_memberships(data.get("vip_memberships", {})),
    }


def write_store(data: dict[str, object]) -> None:
    payload = {
        "users": data.get("users", []),
        "paid_users": [normalize_email(item) for item in data.get("paid_users", []) if normalize_email(item)],
        "vip_memberships": normalize_vip_memberships(data.get("vip_memberships", {})),
    }
    DATA_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def membership_is_active(membership: dict[str, str]) -> bool:
    from datetime import datetime

    expires_at = str(membership.get("expires_at", "")).strip()
    if not expires_at:
        return False
    try:
        expires_date = datetime.fromisoformat(expires_at).date()
    except ValueError:
        return False
    return expires_date >= datetime.now().date()


def prune_expired_paid_users(data: dict[str, object]) -> dict[str, object]:
    vip_memberships = normalize_vip_memberships(data.get("vip_memberships", {}))
    paid_users = [normalize_email(item) for item in data.get("paid_users", []) if normalize_email(item)]
    active_paid_users = [
        email for email in paid_users if membership_is_active(vip_memberships.get(email, {}))
    ]
    if active_paid_users == paid_users:
        data["vip_memberships"] = vip_memberships
        return data

    updated = {
        "users": data.get("users", []),
        "paid_users": active_paid_users,
        "vip_memberships": vip_memberships,
    }
    write_store(updated)
    return updated


def add_paid_user(email, days: int = 30):
    ensure_file()
    data = prune_expired_paid_users(read_store())
    normalized_email = normalize_email(email)
    if not normalized_email:
        return

    paid_users = list(data.get("paid_users", []))
    vip_memberships = dict(data.get("vip_memberships", {}))

    if normalized_email not in paid_users:
        paid_users.append(normalized_email)

    started_at = datetime_now_date_iso()
    vip_memberships[normalized_email] = {
        "started_at": started_at,
        "expires_at": add_days_iso(started_at, days),
    }

    write_store(
        {
            "users": data.get("users", []),
            "paid_users": paid_users,
            "vip_memberships": vip_memberships,
        }
    )


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def email_is_paid(email: str) -> bool:
    normalized_email = normalize_email(email)
    if not normalized_email:
        return False

    data = prune_expired_paid_users(read_store())
    paid_users = set(data.get("paid_users", []))
    if normalized_email not in paid_users:
        return False

    vip_memberships = dict(data.get("vip_memberships", {}))
    return membership_is_active(vip_memberships.get(normalized_email, {}))


def verify_ipn_signature(request_body: bytes, signature: str) -> bool:
    if not NOWPAYMENTS_IPN_SECRET or not signature:
        return False

    computed = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


def verify_lemon_signature(request_body: bytes, signature: str) -> bool:
    if not LEMON_WEBHOOK_SECRET or not signature:
        return False

    computed = hmac.new(
        LEMON_WEBHOOK_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


def verify_sync_secret(request: Request) -> None:
    if not WEBHOOK_SYNC_SECRET:
        return

    provided_secret = str(request.headers.get("x-webhook-sync-secret", "") or "")
    if not provided_secret or not hmac.compare_digest(provided_secret, WEBHOOK_SYNC_SECRET):
        raise HTTPException(status_code=401, detail="Invalid sync secret")


async def handle_nowpayments_ipn(request: Request, require_signature: bool = False):
    raw_body = await request.body()
    payload = json.loads(raw_body)
    print("CRYPTO PAYLOAD:", payload)

    if require_signature:
        signature = request.headers.get("x-nowpayments-sig", "")
        if not verify_ipn_signature(raw_body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payment_status = payload.get("payment_status")
    order_id = payload.get("order_id")

    if payment_status == "finished" and order_id:
        add_paid_user(order_id)

    return {"ok": True}


@app.post("/lemons/webhook")
async def webhook(request: Request):
    if not LEMON_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Lemon webhook secret not configured")

    raw_body = await request.body()
    payload = json.loads(raw_body)
    print("LEMON PAYLOAD:", payload)

    signature = request.headers.get("x-signature", "")
    if not verify_lemon_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    meta = payload.get("meta", {}) or {}
    custom_data = meta.get("custom_data", {}) or {}
    attributes = payload.get("data", {}).get("attributes", {}) or {}
    event_name = str(meta.get("event_name", "") or request.headers.get("x-event-name", "")).strip().lower()
    status = str(attributes.get("status", "")).strip().lower()

    email = normalize_email(
        custom_data.get("google_email")
        or custom_data.get("email")
        or attributes.get("user_email")
        or attributes.get("customer_email")
        or attributes.get("email")
    )
    print("LEMON EVENT:", event_name, "EMAIL:", email, "STATUS:", status)

    paid_events = {
        "order_created",
        "subscription_created",
        "subscription_updated",
        "subscription_resumed",
        "subscription_unpaused",
        "subscription_plan_changed",
        "subscription_payment_success",
        "subscription_payment_recovered",
    }
    paid_statuses = {"paid", "active", "on_trial", "cancelled"}

    if email and event_name in paid_events and (not status or status in paid_statuses):
        add_paid_user(email)

    return {"ok": True}


@app.post("/nowpayments/webhook")
async def nowpayments_webhook(request: Request):
    return await handle_nowpayments_ipn(request, require_signature=True)


@app.get("/vip-status")
async def vip_status(email: str, request: Request):
    verify_sync_secret(request)
    return {"paid": email_is_paid(email)}
