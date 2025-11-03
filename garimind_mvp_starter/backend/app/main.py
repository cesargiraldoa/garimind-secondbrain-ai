from fastapi import FastAPI
from .api.routes import router
from .api.google import router as google_router
from .api.microsoft import router as ms_router
from .api.ai import router as ai_router

app = FastAPI(title="GariMind MVP API")

app.include_router(router)
app.include_router(google_router)
app.include_router(ms_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {"ok": True, "service": "GariMind MVP API"}
