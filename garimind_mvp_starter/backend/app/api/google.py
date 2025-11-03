import os, json, datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

router = APIRouter(prefix="/api/google", tags=["google"])

CREDS_DIR = "data/creds"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_PATH = os.getenv("GOOGLE_REDIRECT_PATH", "/api/google/oauth2/callback")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
REDIRECT_URI = APP_BASE_URL + GOOGLE_REDIRECT_PATH

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid", "email", "profile"
]

def client_config():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Faltan GOOGLE_CLIENT_ID/SECRET en .env")
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }

def token_path():
    return os.path.join(CREDS_DIR, "google_token.json")

def load_creds():
    p = token_path()
    if os.path.exists(p):
        with open(p, "r") as f:
            data = json.load(f)
        return Credentials.from_authorized_user_info(data, SCOPES)
    return None

def save_creds(creds: Credentials):
    os.makedirs(CREDS_DIR, exist_ok=True)
    with open(token_path(), "w") as f:
        f.write(creds.to_json())

@router.get("/auth-url")
def auth_url():
    flow = Flow.from_client_config(client_config(), scopes=SCOPES, redirect_uri=REDIRECT_URI)
    url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return {"auth_url": url, "state": state}

@router.get("/oauth2/callback")
def oauth2_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
    flow = Flow.from_client_config(client_config(), scopes=SCOPES, redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_creds(creds)
    return RedirectResponse(url="/docs")

@router.get("/drive/recent")
def drive_recent():
    creds = load_creds()
    if not creds:
        raise HTTPException(status_code=401, detail="Conecta Google primero (/api/google/auth-url)")
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(
        pageSize=10, fields="files(id, name, modifiedTime, webViewLink)",
        orderBy="modifiedTime desc"
    ).execute()
    return results.get("files", [])

@router.get("/calendar/today")
def calendar_today():
    creds = load_creds()
    if not creds:
        raise HTTPException(status_code=401, detail="Conecta Google primero (/api/google/auth-url)")
    service = build("calendar", "v3", credentials=creds)
    now = datetime.datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = (now.replace(hour=23, minute=59, second=59, microsecond=0)).isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary", timeMin=start, timeMax=end, singleEvents=True, orderBy="startTime"
    ).execute()
    return events_result.get("items", [])

# === Gmail ===
from googleapiclient.discovery import build as gbuild

@router.get("/gmail/inbox")
def gmail_inbox(max_results: int = 50):
    creds = load_creds()
    if not creds:
        raise HTTPException(status_code=401, detail="Conecta Google primero (/api/google/auth-url)")
    service = gbuild("gmail", "v1", credentials=creds)
    msgs_meta = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=max_results).execute()
    ids = [m["id"] for m in msgs_meta.get("messages", [])]
    items = []
    for mid in ids:
        m = service.users().messages().get(userId="me", id=mid, format="metadata", metadataHeaders=["From","Subject","Date"]).execute()
        headers = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
        snippet = m.get("snippet", "")
        items.append({
            "id": mid,
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "snippet": snippet
        })
    return items

@router.get("/gmail/unread")
def gmail_unread(max_results: int = 50):
    creds = load_creds()
    if not creds:
        raise HTTPException(status_code=401, detail="Conecta Google primero (/api/google/auth-url)")
    service = gbuild("gmail", "v1", credentials=creds)
    msgs_meta = service.users().messages().list(userId="me", q="is:unread in:inbox", maxResults=max_results).execute()
    ids = [m["id"] for m in msgs_meta.get("messages", [])]
    items = []
    for mid in ids:
        m = service.users().messages().get(userId="me", id=mid, format="metadata", metadataHeaders=["From","Subject","Date"]).execute()
        headers = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
        snippet = m.get("snippet", "")
        items.append({
            "id": mid,
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "snippet": snippet
        })
    return items
