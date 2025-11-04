import os
import requests
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# =========================================
# Router
# =========================================
router = APIRouter(prefix="/api/ai", tags=["ai"])

# =========================================
# Config desde entorno
# =========================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # usa tu "gpt-5-thinking" si quieres
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

# =========================================
# Cliente OpenAI (lazy)
# =========================================
_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    """Devuelve el cliente de OpenAI inicializado (lazy)."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=400, detail="Falta OPENAI_API_KEY en variables de entorno")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

# =========================================
# Herramientas que el modelo puede invocar
# (formato compatible con la API Responses de OpenAI)
# =========================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_today_unified",
            "description": "Devuelve emails de hoy (Gmail/Outlook), eventos (Google/Outlook) y archivos recientes de Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_emails": {"type": "integer", "description": "Máximo de correos a traer"},
                    "max_drive": {"type": "integer", "description": "Máximo de items de Drive a traer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Crea una tarea en GariMind.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "proyecto_id": {"type": "integer"},
                    "fecha_limite": {"type": "string", "description": "YYYY-MM-DD opcional"}
                },
                "required": ["titulo"]
            }
        }
    },
]

def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecución real de las herramientas del lado servidor."""
    try:
        if name == "get_today_unified":
            r = requests.get(
                f"{APP_BASE_URL}/api/unified/today",
                params={
                    "max_emails": int(args.get("max_emails", 50)),
                    "max_drive": int(args.get("max_drive", 10)),
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

        if name == "create_task":
            # Puedes redirigir a tu endpoint real de creación de tareas
            # Aquí se usa task_from_email como base (ajústalo si tienes otro)
            r = requests.post(
                f"{APP_BASE_URL}/api/actions/task_from_email",
                json={
                    "titulo": args.get("titulo"),
                    "proyecto_id": args.get("proyecto_id"),
                    "fecha_limite": args.get("fecha_limite"),
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

        return {"error": f"tool '{name}' not found"}

    except requests.HTTPError as re:
        return {"error": f"HTTP error calling tool '{name}': {str(re)}"}
    except Exception as e:
        return {"error": f"error calling tool '{name}': {str(e)}"}

# =========================================
# Modelos de entrada
# =========================================
class ReasonIn(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None  # por si luego quieres enriquecer

class ChatIn(BaseModel):
    prompt: str

# =========================================
# Utilidades internas para Responses API
# =========================================
def _extract_tool_calls(resp_obj) -> List[Dict[str, Any]]:
    """
    Extrae tool calls de la respuesta de la Responses API.
    resp_obj.output suele ser una lista de bloques; buscamos type == "tool_call".
    """
    found: List[Dict[str, Any]] = []
    out = getattr(resp_obj, "output", None)
    if isinstance(out, list):
        for block in out:
            if getattr(block, "type", "") == "tool_call":
                found.append({
                    "id": block.id,
                    "name": block.tool.name,
                    "arguments": block.tool.arguments or {}
                })
    return found

def _output_text(resp_obj) -> str:
    """
    Toma el texto final de la respuesta (output_text) o arma uno básico.
    """
    txt = getattr(resp_obj, "output_text", None)
    return txt or "Listo."

# =========================================
# Endpoint principal de razonamiento
# =========================================
@router.post("/reason")
def reason(payload: ReasonIn):
    """
    Motor de razonamiento de GariMind. El modelo puede llamar herramientas
    para leer el 'hoy unificado' o crear tareas, y luego produce una respuesta final.
    """
    cli = get_client()

    # 1) Primer pase: permitir que el modelo decida si usar herramientas
    first = cli.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "Eres Gari, el Motor de Razonamiento de GariMind Second Brain CésarStyle™. "
                    "Piensas de forma estratégica y humana; si te ayuda, llama herramientas. "
                    "Sé práctico, claro, cálido y accionable."
                ),
            },
            {"role": "user", "content": payload.prompt},
        ],
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.2,
    )

    # 2) Si hay llamadas a herramientas, las resolvemos (hasta 2 hops)
    tool_outputs: List[Dict[str, Any]] = []
    calls = _extract_tool_calls(first)
    hops = 0

    while calls and hops < 2:
        hops += 1
        # Ejecutar cada tool y recolectar
        for c in calls:
            result = call_tool(c["name"], c["arguments"])
            tool_outputs.append({
                "call_id": c["id"],
                "name": c["name"],
                "output": result,
            })

        # 3) Nuevo pase aportando los resultados como bloques "tool"
        second = cli.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": "Eres GariMind, un razonador ejecutivo y cálido."},
                {"role": "user", "content": payload.prompt},
                *[
                    {
                        "role": "tool",
                        "name": o["name"],
                        "tool_call_id": o["call_id"],
                        "content": str(o["output"]),
                    }
                    for o in tool_outputs
                ],
            ],
            tools=TOOLS,
            tool_choice="none",
            temperature=0.2,
        )

        # Ver si el modelo quiere hacer más tool-calls
        calls = _extract_tool_calls(second)
        if not calls:
            # ya no hay tool-calls → tomar texto final
            answer = _output_text(second)
            return {"answer": answer, "tools_used": [o["name"] for o in tool_outputs]}

    # Si no hubo calls en el primer pase:
    final_text = _output_text(first)
    return {"answer": final_text, "tools_used": []}

# =========================================
# Alias compatible: /api/ai/chat  → reutiliza /reason
# =========================================
@router.post("/chat")
def chat(payload: ChatIn):
    """Alias para compatibilidad con frontends que llaman /api/ai/chat."""
    return reason(ReasonIn(prompt=payload.prompt))
