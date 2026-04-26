import json, os
import urllib.request
from fastapi import FastAPI, Request

app = FastAPI()

DATA_PATH = "emails.json"


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


@app.post("/lemons/webhook")
async def webhook(request: Request):
    payload = await request.json()
    print("WEBHOOK PAYLOAD:", payload)

    data = payload.get("data", {}).get("attributes", {})

    email = (
        data.get("user_email")
        or data.get("customer_email")
        or data.get("email")
    )
    print("EXTRACTED EMAIL:", email)

    if email:
        add_paid_user(email)
        try:
            urllib.request.urlopen(f"https://girlpire.streamlit.app/?vip_email={email}")
        except Exception as e:
            print("ERROR:", e)

    return {"ok": True}
