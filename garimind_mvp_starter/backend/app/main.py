# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 👇 importa los routers de tu paquete api
from app.api import routes as base_routes
from app.api import google as google_routes
from app.api import microsoft as ms_routes
from app.api import ai as ai_routes

app = FastAPI(title="GariMind Second Brain")

# CORS sencillo (ajusta dominios si quieres)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # pon tus dominios frontend si deseas restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Health & Root ----------
@app.get("/")
def root():
    return {
        "message": "🚀 GariMind Second Brain está en línea y funcionando correctamente",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# --------- Registro de routers ----------
# Rutas base (proyectos, tareas, recuerdos, daily-magnet, inbox, etc.)
app.include_router(base_routes.router)

# Integraciones
app.include_router(google_routes.router)
app.include_router(ms_routes.router)

# Motor de razonamiento (OpenAI)
app.include_router(ai_routes.router)
