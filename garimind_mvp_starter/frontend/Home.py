import streamlit as st
import requests
import os
from dotenv import load_dotenv

# =============================
# 🔧 Configuración
# =============================
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "https://garimind-secondbrain-ai.onrender.com")

st.set_page_config(page_title="🧠 GariMind • Daily Magnet", layout="wide", page_icon="🧲")

# =============================
# 🧲 Encabezado
# =============================
st.title("🧲 Daily Magnet")
st.caption("Lo de ayer • Lo crítico de hoy • Recuerdo • Frase de bondad")

# =============================
# 📊 Bloque Daily Magnet
# =============================
try:
    dm = requests.get(f"{BACKEND_URL}/api/daily-magnet", timeout=10).json()
    cols = st.columns(4)
    cols[0].metric("Ayer", dm.get("ayer", "-"))
    cols[1].metric("Hoy", dm.get("hoy", "-"))
    cols[2].metric("Recuerdo", dm.get("recuerdo", "-"))
    cols[3].metric("Bondad", dm.get("frase_bondad", "-"))
except Exception as e:
    st.error(f"No pude cargar el Daily Magnet: {e}")
    st.info("Verifica que el backend esté disponible o la variable BACKEND_URL sea correcta.")

st.divider()

# =============================
# 📝 Captura rápida
# =============================
st.subheader("📥 Captura rápida desde Inbox")

entrada = st.text_input("Escribe algo para convertirlo en tarea o recuerdo", placeholder="Ej: Llamar a proveedor / Recordar enviar informe...")

colA, colB, colC = st.columns([1, 1, 2])
tipo = colA.selectbox("Tipo", ["tarea", "recuerdo"])
proyecto_id = colB.number_input("Proyecto ID (opcional)", min_value=0, step=1)
enviar = colC.button("🚀 Capturar ahora")

if enviar:
    if entrada.strip() == "":
        st.warning("Por favor escribe algo antes de enviar.")
    else:
        try:
            payload = {
                "entrada": entrada,
                "como": tipo,
                "proyecto_id": int(proyecto_id) if proyecto_id else None
            }
            r = requests.post(f"{BACKEND_URL}/api/inbox/capturar", json=payload, timeout=10)
            if r.status_code in [200, 201]:
                st.success(f"✅ Capturado correctamente: {r.json()}")
            else:
                st.error(f"⚠️ Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"❌ Error al enviar: {e}")

st.divider()

# =============================
# 🔁 Sección: Lista de tareas y recuerdos
# =============================
st.subheader("📋 Últimas tareas y recuerdos")

col1, col2 = st.columns(2)

with col1:
    st.write("### ✅ Tareas")
    try:
        tareas = requests.get(f"{BACKEND_URL}/api/tareas").json()
        if tareas:
            for t in tareas:
                st.write(f"- {t.get('title', 'Sin título')} (id: {t.get('id')})")
        else:
            st.info("No hay tareas registradas.")
    except Exception as e:
        st.error(f"Error al obtener tareas: {e}")

with col2:
    st.write("### 💭 Recuerdos")
    try:
        recuerdos = requests.get(f"{BACKEND_URL}/api/recuerdos").json()
        if recuerdos:
            for r in recuerdos:
                st.write(f"- {r.get('texto', 'Sin texto')} (id: {r.get('id')})")
        else:
            st.info("No hay recuerdos aún.")
    except Exception as e:
        st.error(f"Error al obtener recuerdos: {e}")

st.divider()
st.caption("Desarrollado con 💙 por CésarStyle™ — GariMind Second Brain")
