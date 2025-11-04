import os
import requests
import streamlit as st

st.set_page_config(page_title="Gari • Chat", layout="wide")

# ✅ URL base del backend (solo la raíz, sin /api ni /Chat)
BACKEND_URL = os.getenv("BACKEND_URL", "https://garimind-secondbrain-ai.onrender.com")

st.title("💬 Gari • Motor de Razonamiento")
prompt = st.text_input(
    "Pídele algo a Gari (ej: 'Revisa mi día y sugiere 3 tareas críticas')",
    "Hola, ¿por qué te llamas Gari?"
)

if st.button("Enviar"):
    try:
        url = f"{BACKEND_URL}/api/ai/reason"   # o /api/ai/chat (ambos son POST)
        st.info(f"📡 Enviando a: {url}")

        r = requests.post(url, json={"prompt": prompt}, timeout=60)

        # 🩺 Depuración: si no es JSON, mostrar contenido crudo
        ctype = r.headers.get("content-type", "")
        if "application/json" not in ctype:
            st.error(f"❌ El backend no devolvió JSON (HTTP {r.status_code}).")
            st.code(r.text[:2000], language="text")
        else:
            data = r.json()
            st.success(data.get("answer", "(sin respuesta)"))
            if data.get("tools_used"):
                st.caption(f"Herramientas usadas: {', '.join(data['tools_used'])}")

    except Exception as e:
        st.error(f"Error llamando al backend: {e}")
        st.info(f"URL usada: {url}")
