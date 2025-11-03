import streamlit as st
import requests, os
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="GariMind • Daily Magnet", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("🧲 Daily Magnet")
st.caption("Lo de ayer • Lo crítico de hoy • Recuerdo • Frase de bondad")

try:
    dm = requests.get(f"{BACKEND_URL}/api/daily-magnet", timeout=5).json()
    cols = st.columns(4)
    cols[0].metric("Ayer", dm.get("ayer", "-"))
    cols[1].metric("Hoy", dm.get("hoy", "-"))
    cols[2].metric("Recuerdo", dm.get("recuerdo", "-"))
    cols[3].metric("Bondad", dm.get("frase_bondad", "-"))
except Exception as e:
    st.error(f"No pude cargar el Daily Magnet: {e}")
    st.info("Verifica que el backend esté en http://localhost:8000")

st.divider()
st.subheader("Captura rápida")
entrada = st.text_input("Escribe algo y conviértelo en tarea o recuerdo")
colA, colB, colC = st.columns([1,1,2])
tipo = colA.selectbox("Como", ["tarea", "recuerdo"])
proyecto_id = colB.number_input("Proyecto ID (opcional)", min_value=0, step=1)

if colC.button("Crear desde Inbox"):
    try:
        r = requests.post(f"{BACKEND_URL}/api/inbox/capturar", json={"entrada": entrada, "como": tipo, "proyecto_id": int(proyecto_id) if proyecto_id else None})
        st.success(f"Creado: {r.json()}")
    except Exception as e:
        st.error(e)
