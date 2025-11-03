import os, json, datetime, requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import msal

router = APIRouter(prefix="/api/ms", tags=["microsoft"])

CREDS_DIR = "data/creds"
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_TENANT = os.getenv("MS_TENANT", "common")
MS_REDIRECT_PATH = os.getenv("MS_REDIRECT_PATH", "/api/ms/oauth2/callback")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
REDIRECT_URI = APP_BASE_URL + MS_REDIRECT_PATH
AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT}"
SCOPE = ["Calendars.Read", "Mail.Read", "offline_access", "openid", "profile", "email"]
GRAPH = "https://graph.microsoft.com/v1.0"

def token_path():
    return os.path.join(CREDS_DIR, "ms_token.json")

def save_token(token: dict):
    os.makedirs(CREDS_DIR, exist_ok=True)
    with open(token_path(), "w") as f:
        json.dump(token, f)

def load_token():
    p = token_path()
    if os.path.exists(p):
        with open(p, "r") as f:
            return json.load(f)
    return None

def build_app():
    if not MS_CLIENT_ID or not MS_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Faltan MS_CLIENT_ID/SECRET en .env")
    return msal.ConfidentialClientApplication(
        MS_CLIENT_ID, authority=AUTHORITY, client_credential=MS_CLIENT_SECRET
    )

@router.get("/auth-url")
def auth_url():
    app = build_app()
    url = app.get_authorization_request_url(SCOPE, redirect_uri=REDIRECT_URI)
    return {"auth_url": url}

@router.get("/oauth2/callback")
def oauth2_callback(code: str | None = None):
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
    app = build_app()
    token = app.acquire_token_by_authorization_code(code, scopes=SCOPE, redirect_uri=REDIRECT_URI)
    if "access_token" not in token:
        raise HTTPException(status_code=400, detail=f"Token error: {token}")
    save_token(token)
    return RedirectResponse(url="/docs")

def ensure_access_token():
    token = load_token()
    if not token:
        raise HTTPException(status_code=401, detail="Conecta Microsoft primero (/api/ms/auth-url)")
    # naive refresh support if refresh_token present (msal will handle it in acquire_token_by_refresh_token)
    if token.get("expires_in", 3600) < 60 and "refresh_token" in token:
        app = build_app()
        new_token = app.acquire_token_by_refresh_token(token["refresh_token"], scopes=SCOPE)
        if "access_token" in new_token:
            save_token(new_token)
            token = new_token
    return token["access_token"]

@router.get("/calendar/today")
def calendar_today():
    access = ensure_access_token()
    headers = {"Authorization": f"Bearer {access}"}
    now = datetime.datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()+"Z"
    end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()+"Z"
    params = {"startDateTime": start, "endDateTime": end, "$orderby": "start/dateTime"}
    r = requests.get(f"https://graph.microsoft.com/v1.0/me/calendarView", headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json().get("value", [])

@router.get("/mail/inbox")
def mail_inbox(top: int = 50):
    access = ensure_access_token()
    headers = {"Authorization": f"Bearer {access}"}
    params = {"$top": str(top), "$select": "sender,subject,receivedDateTime,isRead,bodyPreview", "$orderby": "receivedDateTime desc"}
    r = requests.get(f"{GRAPH}/me/messages", headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json().get("value", [])
    items = []
    for m in data:
        items.append({
            "id": m.get("id"),
            "from": (m.get("sender") or {}).get("emailAddress", {}).get("address"),
            "subject": m.get("subject"),
            "date": m.get("receivedDateTime"),
            "isRead": m.get("isRead"),
            "snippet": m.get("bodyPreview")
        })
    return items

@router.get("/mail/unread")
def mail_unread(top: int = 50):
    access = ensure_access_token()
    headers = {"Authorization": f"Bearer {access}"}
    params = {"$top": str(top), "$select": "sender,subject,receivedDateTime,isRead,bodyPreview", "$orderby": "receivedDateTime desc", "$filter": "isRead eq false"}
    r = requests.get(f"{GRAPH}/me/messages", headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json().get("value", [])
    items = []
    for m in data:
        items.append({
            "id": m.get("id"),
            "from": (m.get("sender") or {}).get("emailAddress", {}).get("address"),
            "subject": m.get("subject"),
            "date": m.get("receivedDateTime"),
            "isRead": m.get("isRead"),
            "snippet": m.get("bodyPreview")
        })
    return items
