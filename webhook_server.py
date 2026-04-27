import hashlib
import hmac
import json
import os

from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

DATA_PATH = "emails.json"
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")


def ensure_file():
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({"users": [], "paid_users": []}, f)


def add_paid_user(email):
    ensure_file()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if email and email not in data.get("paid_users", []):
        data["paid_users"].append(email)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def verify_ipn_signature(request_body: bytes, signature: str) -> bool:
    if not NOWPAYMENTS_IPN_SECRET or not signature:
        return False

    computed = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


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
    return await handle_nowpayments_ipn(request)


@app.post("/nowpayments/webhook")
async def nowpayments_webhook(request: Request):
    return await handle_nowpayments_ipn(request, require_signature=True)
