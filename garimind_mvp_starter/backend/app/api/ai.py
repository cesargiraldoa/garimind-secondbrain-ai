import os, requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from openai import OpenAI

router = APIRouter(prefix="/api/ai", tags=["ai"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-thinking")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

if not OPENAI_API_KEY:
    # No lanzamos excepción aquí para permitir levantar el server sin clave;
    # pero las llamadas a /reason fallarán amistosamente si no hay clave.
    pass

client = None
def get_client():
    global client
    if client is None:
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=400, detail="Falta OPENAI_API_KEY en .env")
        client = OpenAI(api_key=OPENAI_API_KEY)
    return client

# Herramientas que el modelo puede invocar
TOOLS = [
    {"type": "function", "function": {
        "name": "get_today_unified",
        "description": "Devuelve emails hoy (Gmail/Outlook), eventos (Google/Outlook) y Drive recientes",
        "parameters": {"type":"object","properties":{"max_emails":{"type":"integer"},"max_drive":{"type":"integer"}}, "required":[]}
    }},
    {"type": "function", "function": {
        "name": "create_task",
        "description": "Crea una tarea en GariMind",
        "parameters": {"type":"object","properties":{"titulo":{"type":"string"},"proyecto_id":{"type":"integer"},"fecha_limite":{"type":"string"}}, "required":["titulo"]}
    }},
]

def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "get_today_unified":
        r = requests.get(f"{APP_BASE_URL}/api/unified/today", params={
            "max_emails": args.get("max_emails", 50),
            "max_drive": args.get("max_drive", 10)
        }, timeout=30)
        return r.json()
    if name == "create_task":
        # por simplicidad lo dirigimos a task_from_email, sirve igual
        r = requests.post(f"{APP_BASE_URL}/api/actions/task_from_email", json=args, timeout=30)
        return r.json()
    return {"error": f"tool {name} not found"}

class AskIn(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None

@router.post("/reason")
def reason(payload: AskIn):
    cli = get_client()
    # 1) Primer pase: que el modelo decida si usar herramientas
    resp = cli.responses.create(
        model=OPENAI_MODEL,
        input=[{"role":"system","content":"Eres GariMind, un razonador ejecutivo. Usa herramientas cuando te ayuden a responder o a crear tareas."},
               {"role":"user","content": payload.prompt}],
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.2,
    )

    # 2) Procesar tool-calls simples (1–2 hops)
    tool_outputs: List[Dict[str, Any]] = []
    def extract_calls(r) -> List[Dict[str, Any]]:
        calls = []
        out = getattr(r, "output", None)
        if isinstance(out, list):
            for block in out:
                if getattr(block, "type", "") == "tool_call":
                    calls.append({
                        "id": block.id,
                        "name": block.tool.name,
                        "arguments": block.tool.arguments or {}
                    })
        return calls

    calls = extract_calls(resp)
    hops = 0
    while calls and hops < 2:
        hops += 1
        for c in calls:
            result = call_tool(c["name"], c["arguments"])
            tool_outputs.append({"call_id": c["id"], "name": c["name"], "output": result})
        resp = cli.responses.create(
            model=OPENAI_MODEL,
            input=[{"role":"system","content":"Eres GariMind, un razonador ejecutivo."},
                   {"role":"user","content": payload.prompt}] + 
                  [{"role":"tool","name":o["name"], "tool_call_id":o["call_id"], "content":str(o["output"])} for o in tool_outputs],
            tools=TOOLS,
            tool_choice="none",
            temperature=0.2
        )
        calls = extract_calls(resp)

    final_text = getattr(resp, "output_text", None) or "Listo."
    return {"answer": final_text, "tools_used": [o["name"] for o in tool_outputs]}
