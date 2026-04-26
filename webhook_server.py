from fastapi import FastAPI, Request
import json, os

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

    email = payload.get("data", {}).get("attributes", {}).get("user_email")

    if email:
        add_paid_user(email)

    return {"ok": True}
