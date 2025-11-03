import streamlit as st, requests, os
from dotenv import load_dotenv
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Diario Ejecutivo", layout="wide")
st.title("📜 Diario Ejecutivo")

try:
    items = requests.get(f"{BACKEND_URL}/api/diario").json()
    for it in items:
        if it.get("tipo") == "tarea":
            st.write(f"✅ **Tarea**: {it['titulo']} · {it['fecha']} · *{it.get('estado','')}*")
        else:
            st.write(f"🧠 **Recuerdo**: {it['contenido']} · {it['fecha']} · #{it.get('tags','')}")
except Exception as e:
    st.error(f"No pude cargar el diario: {e}")
