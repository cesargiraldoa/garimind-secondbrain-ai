from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
import os, re
from ..core.config import settings
from ..models.models import Proyecto, Tarea, Recuerdo, Interaccion
from ..models.base import Base
from ..db.session import get_session_factory
from datetime import datetime
import pathlib

router = APIRouter(prefix="/api")

SessionFactory = get_session_factory(settings.DATABASE_URL)

# Pydantic schemas
class ProyectoIn(BaseModel):
    nombre: str
    objetivo: Optional[str] = None

class ProyectoOut(BaseModel):
    id: int
    nombre: str
    objetivo: Optional[str] = None
    estado: str
    fecha_inicio: datetime
    class Config:
        from_attributes = True

class TareaIn(BaseModel):
    titulo: str
    responsable: Optional[str] = None
    prioridad: Optional[str] = "media"
    proyecto_id: Optional[int] = None
    fecha_limite: Optional[datetime] = None
    estado: Optional[str] = "abierta"

class TareaOut(BaseModel):
    id: int
    titulo: str
    responsable: Optional[str]
    prioridad: str
    proyecto_id: Optional[int]
    fecha_limite: Optional[datetime]
    estado: str
    creada_en: datetime
    class Config:
        from_attributes = True

class RecuerdoIn(BaseModel):
    tipo: Optional[str] = "profesional"
    contenido: str
    tags: Optional[str] = None
    proyecto_id: Optional[int] = None
    doc_url: Optional[str] = None

class RecuerdoOut(BaseModel):
    id: int
    tipo: str
    contenido: str
    fecha: datetime
    tags: Optional[str]
    proyecto_id: Optional[int]
    doc_url: Optional[str]
    class Config:
        from_attributes = True

class CapturaIn(BaseModel):
    entrada: str
    como: Optional[str] = "tarea"  # tarea | recuerdo
    proyecto_id: Optional[int] = None

def to_slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-\_\s]", "", name).strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s[:60] if s else "proyecto"

# Init DB (create tables)
def init_db():
    from sqlalchemy import create_engine
    from ..db.utils import is_async_url
    url = settings.DATABASE_URL
    if is_async_url(url):
        # create tables with a sync engine for simplicity
        sync_url = url.replace("+aiosqlite", "").replace("postgresql+asyncpg", "postgresql+psycopg2")
        engine = create_engine(sync_url, future=True)
    else:
        engine = create_engine(url, future=True)
    Base.metadata.create_all(bind=engine)

@router.on_event("startup")
def startup():
    init_db()

@router.post("/projects", response_model=ProyectoOut)
def create_project(payload: ProyectoIn):
    with SessionFactory() as session:
        p = Proyecto(nombre=payload.nombre, objetivo=payload.objetivo)
        session.add(p)
        session.commit()
        session.refresh(p)

    # create folder
    projects_dir = settings.DATA_DIR
    pathlib.Path(projects_dir).mkdir(parents=True, exist_ok=True)
    folder = pathlib.Path(projects_dir) / to_slug(payload.nombre)
    folder.mkdir(parents=True, exist_ok=True)

    return p

@router.get("/projects", response_model=List[ProyectoOut])
def list_projects():
    with SessionFactory() as session:
        res = session.execute(select(Proyecto).order_by(Proyecto.fecha_inicio.desc()))
        return [r[0] for r in res.all()]

@router.post("/tareas", response_model=TareaOut)
def create_tarea(payload: TareaIn):
    with SessionFactory() as session:
        t = Tarea(**payload.model_dump())
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

@router.get("/tareas", response_model=List[TareaOut])
def list_tareas(proyecto_id: Optional[int] = None, estado: Optional[str] = None):
    with SessionFactory() as session:
        stmt = select(Tarea)
        if proyecto_id:
            stmt = stmt.where(Tarea.proyecto_id == proyecto_id)
        if estado:
            stmt = stmt.where(Tarea.estado == estado)
        stmt = stmt.order_by(Tarea.creada_en.desc())
        res = session.execute(stmt).scalars().all()
        return res

@router.post("/recuerdos", response_model=RecuerdoOut)
def create_recuerdo(payload: RecuerdoIn):
    with SessionFactory() as session:
        r = Recuerdo(**payload.model_dump())
        session.add(r)
        session.commit()
        session.refresh(r)
        return r

@router.get("/recuerdos", response_model=List[RecuerdoOut])
def list_recuerdos(tag: Optional[str] = None, q: Optional[str] = None, proyecto_id: Optional[int] = None):
    with SessionFactory() as session:
        stmt = select(Recuerdo)
        if proyecto_id:
            stmt = stmt.where(Recuerdo.proyecto_id == proyecto_id)
        if tag:
            stmt = stmt.where(Recuerdo.tags.ilike(f"%{tag}%"))
        if q:
            stmt = stmt.where(Recuerdo.contenido.ilike(f"%{q}%"))
        stmt = stmt.order_by(Recuerdo.fecha.desc())
        res = session.execute(stmt).scalars().all()
        return res

@router.get("/daily-magnet")
def daily_magnet():
    # Mock básico
    return {
        "ayer": "Cerraste 3 tareas y agregaste 1 recuerdo clave.",
        "hoy": "Revisión de Dentisalud a las 9:00 y preparar DAFO.",
        "recuerdo": "‘El liderazgo también es esperar por quien no puede caminar solo.’",
        "frase_bondad": "Respira. Hoy también puedes empezar pequeño y terminar grande."
    }

@router.get("/diario")
def diario(desde: Optional[str] = None, hasta: Optional[str] = None):
    # Demo: junta cambios recientes de tareas y recuerdos
    with SessionFactory() as session:
        tareas = session.execute(select(Tarea).order_by(Tarea.creada_en.desc()).limit(20)).scalars().all()
        recuerdos = session.execute(select(Recuerdo).order_by(Recuerdo.fecha.desc()).limit(20)).scalars().all()
    timeline = []
    for t in tareas:
        timeline.append({"tipo": "tarea", "titulo": t.titulo, "fecha": t.creada_en.isoformat(), "estado": t.estado})
    for r in recuerdos:
        timeline.append({"tipo": "recuerdo", "contenido": r.contenido, "fecha": r.fecha.isoformat(), "tags": r.tags})
    return sorted(timeline, key=lambda x: x["fecha"], reverse=True)

@router.post("/inbox/capturar")
def capturar(payload: CapturaIn):
    # Si como=tarea -> crea una Tarea; si como=recuerdo -> crea Recuerdo
    if payload.como == "recuerdo":
        with SessionFactory() as session:
            r = Recuerdo(contenido=payload.entrada, proyecto_id=payload.proyecto_id)
            session.add(r)
            session.commit()
            session.refresh(r)
            return {"tipo":"recuerdo","id": r.id}
    else:
        with SessionFactory() as session:
            t = Tarea(titulo=payload.entrada, proyecto_id=payload.proyecto_id)
            session.add(t)
            session.commit()
            session.refresh(t)
            return {"tipo":"tarea","id": t.id}


# === Unified 'today' and quick-actions ===
from fastapi import Body
from typing import Dict, Any
from .google import load_creds as g_load_creds
from .microsoft import ensure_access_token
from googleapiclient.discovery import build as gbuild
import requests as _requests
import datetime as _dt

@router.get("/unified/today")
def unified_today(max_emails: int = 50, max_drive: int = 10):
    out: Dict[str, Any] = {"gmail": [], "outlook_mail": [], "gcal": [], "mscal": [], "drive": []}

    # Gmail (optional)
    try:
        gcreds = g_load_creds()
        if gcreds:
            gsvc = gbuild("gmail", "v1", credentials=gcreds)
            msgs_meta = gsvc.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=max_emails).execute()
            ids = [m["id"] for m in msgs_meta.get("messages", [])]
            gmails = []
            for mid in ids:
                m = gsvc.users().messages().get(userId="me", id=mid, format="metadata", metadataHeaders=["From","Subject","Date"]).execute()
                hdrs = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
                gmails.append({"id": mid, "from": hdrs.get("From"), "subject": hdrs.get("Subject"), "date": hdrs.get("Date"), "snippet": m.get("snippet","")})
            out["gmail"] = gmails
    except Exception as e:
        out["gmail_error"] = str(e)

    # Outlook Mail (optional)
    try:
        access = ensure_access_token()
        if access:
            headers = {"Authorization": f"Bearer {access}"}
            params = {"$top": str(max_emails), "$select": "sender,subject,receivedDateTime,isRead,bodyPreview", "$orderby": "receivedDateTime desc"}
            r = _requests.get("https://graph.microsoft.com/v1.0/me/messages", headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json().get("value", [])
                om = []
                for m in data:
                    om.append({
                        "id": m.get("id"),
                        "from": (m.get("sender") or {}).get("emailAddress", {}).get("address"),
                        "subject": m.get("subject"),
                        "date": m.get("receivedDateTime"),
                        "isRead": m.get("isRead"),
                        "snippet": m.get("bodyPreview")
                    })
                out["outlook_mail"] = om
    except Exception as e:
        out["outlook_mail_error"] = str(e)

    # Google Calendar today
    try:
        gcreds = g_load_creds()
        if gcreds:
            cal = gbuild("calendar", "v3", credentials=gcreds)
            now = _dt.datetime.utcnow()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
            end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"
            evs = cal.events().list(calendarId="primary", timeMin=start, timeMax=end, singleEvents=True, orderBy="startTime").execute().get("items", [])
            out["gcal"] = evs
    except Exception as e:
        out["gcal_error"] = str(e)

    # Outlook Calendar today
    try:
        access = ensure_access_token()
        if access:
            headers = {"Authorization": f"Bearer {access}"}
            now = _dt.datetime.utcnow()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()+"Z"
            end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()+"Z"
            params = {"startDateTime": start, "endDateTime": end, "$orderby": "start/dateTime"}
            r = _requests.get("https://graph.microsoft.com/v1.0/me/calendarView", headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                out["mscal"] = r.json().get("value", [])
    except Exception as e:
        out["mscal_error"] = str(e)

    # Google Drive recent
    try:
        gcreds = g_load_creds()
        if gcreds:
            drv = gbuild("drive", "v3", credentials=gcreds)
            files = drv.files().list(pageSize=max_drive, fields="files(id, name, modifiedTime, webViewLink)", orderBy="modifiedTime desc").execute().get("files", [])
            out["drive"] = files
    except Exception as e:
        out["drive_error"] = str(e)

    return out

class QuickTaskIn(BaseModel):
    titulo: str
    proyecto_id: int | None = None
    fecha_limite: datetime | None = None

@router.post("/actions/task_from_email")
def task_from_email(data: QuickTaskIn = Body(...)):
    # create a Tarea from an email summary (subject, optional link)
    with SessionFactory() as session:
        t = Tarea(titulo=data.titulo, proyecto_id=data.proyecto_id, fecha_limite=data.fecha_limite)
        session.add(t)
        session.commit()
        session.refresh(t)
        return {"ok": True, "tarea_id": t.id}

@router.post("/actions/task_from_event")
def task_from_event(data: QuickTaskIn = Body(...)):
    with SessionFactory() as session:
        t = Tarea(titulo=data.titulo, proyecto_id=data.proyecto_id, fecha_limite=data.fecha_limite)
        session.add(t)
        session.commit()
        session.refresh(t)
        return {"ok": True, "tarea_id": t.id}
