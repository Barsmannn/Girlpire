# Girlpire

Streamlit SaaS app for creator income optimization.

## Project files

- `app.py`
- `requirements.txt`
- `emails.json`
- `.gitignore`

`emails.json` is auto-created by the app if it does not exist.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

If `streamlit` is not available in your terminal PATH, use:

```bash
python -m streamlit run app.py
```

## Secrets

Do not commit real secrets. Keep them in one of these places:

- `.streamlit/secrets.toml` for Streamlit auth and cloud secrets
- `.env` for local environment variables such as `RESEND_API_KEY`

The included `.gitignore` already excludes both `.env` and `.streamlit/secrets.toml`.

## Google Login

The app uses native Streamlit authentication with:

- `st.login("google")`
- `st.user`
- `st.logout()`

Local `.streamlit/secrets.toml` example:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "REPLACE_WITH_RANDOM_STRING"

[auth.google]
client_id = "PASTE_YOUR_CLIENT_ID_HERE"
client_secret = "PASTE_YOUR_CLIENT_SECRET_HERE"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Set the Google OAuth redirect URI to:

```text
http://localhost:8501/oauth2callback
```

## Streamlit Community Cloud

1. Push the project to GitHub.
2. Deploy the repo in Streamlit Community Cloud.
3. Add the same auth values inside the app Secrets panel.
4. Add any optional secrets you use, such as LemonSqueezy or Groq keys.

If secrets are missing, the app shows a clear warning instead of crashing.

## Secure LemonSqueezy webhook

The app reads VIP access from `emails.json`. To mark paying users securely, deploy `webhook_server.py` separately on a host such as Render or Fly.io.

Set this environment variable on the webhook host:

```text
LEMON_WEBHOOK_SECRET=your_webhook_signing_secret
```

Then in LemonSqueezy:

1. Open `Settings -> Webhooks`
2. Add your public endpoint, for example:
   `https://your-app.onrender.com/lemons/webhook`
3. Copy the LemonSqueezy signing secret into `LEMON_WEBHOOK_SECRET`

This avoids using URL-based VIP unlocks and only grants VIP after a verified webhook event.
