# garimind_mvp_starter/backend/app/main.py

from fastapi import FastAPI
from .api.routes import router
from .api.google import router as google_router
from .api.microsoft import router as ms_router
from .api.ai import router as ai_router

app = FastAPI(
    title="GariMind MVP API",
    version="1.0.0",
    description="API central de GariMind Second Brain — Conexión IA, Google, Microsoft y módulos analíticos."
)

# 🔹 Routers principales
app.include_router(router, prefix="/api")
app.include_router(google_router, prefix="/api")
app.include_router(ms_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

# 🔹 Rutas raíz y de salud (para Render)
@app.get("/")
def root():
    return {
        "message": "🚀 GariMind Second Brain está en línea y funcionando correctamente",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    return {"ok": True, "status": "healthy", "service": "GariMind MVP API"}

# 🔹 Ejemplo de endpoint adicional para verificación rápida
@app.get("/ping")
def ping():
    return {"pong": "ok"}
