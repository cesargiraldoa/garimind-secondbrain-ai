import streamlit as st, requests, os, pandas as pd
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Hoy • Hub", layout="wide")
st.title("🗓️📁📬 Hoy — Hub unificado")

with st.spinner("Cargando..."):
    try:
        data = requests.get(f"{BACKEND_URL}/api/unified/today", params={"max_emails": 50, "max_drive": 10}).json()
    except Exception as e:
        st.error(f"No pude cargar el hub: {e}")
        st.stop()

# Calendarios
c1, c2 = st.columns(2)
with c1:
    st.subheader("Google Calendar — Hoy")
    gcal = data.get("gcal", [])
    if gcal: st.dataframe(pd.DataFrame(gcal))
    else: st.info("Sin eventos o sin autorización.")
with c2:
    st.subheader("Outlook Calendar — Hoy")
    mscal = data.get("mscal", [])
    if mscal: st.dataframe(pd.DataFrame(mscal))
    else: st.info("Sin eventos o sin autorización.")

st.divider()

# Emails
e1, e2 = st.columns(2)
with e1:
    st.subheader("Gmail — Inbox (50)")
    gmail = data.get("gmail", [])
    if gmail: st.dataframe(pd.DataFrame(gmail))
    else: st.info("Sin correos o sin autorización.")
with e2:
    st.subheader("Outlook — Inbox (50)")
    outlook = data.get("outlook_mail", [])
    if outlook: st.dataframe(pd.DataFrame(outlook))
    else: st.info("Sin correos o sin autorización.")

st.divider()

# Drive
st.subheader("Google Drive — Recientes (10)")
drv = data.get("drive", [])
if drv: st.dataframe(pd.DataFrame(drv))
else: st.info("Sin archivos o sin autorización.")

st.divider()
st.subheader("⚡ Acciones rápidas: crear tarea desde correo / evento")

with st.form("quick_task"):
    fuente = st.selectbox("Fuente", ["Gmail", "Outlook Mail", "Google Calendar", "Outlook Calendar", "Otro"])
    titulo = st.text_input("Título de la tarea (sujeto del correo o título del evento)")
    proyecto_id = st.number_input("Proyecto ID (opcional)", min_value=0, step=1)
    fecha_limite = st.text_input("Fecha límite (YYYY-MM-DD HH:MM, opcional)", "")
    submitted = st.form_submit_button("Crear tarea")

    if submitted and titulo.strip():
        payload = {"titulo": titulo, "proyecto_id": int(proyecto_id) if proyecto_id else None}
        if fecha_limite.strip():
            try:
                dt = datetime.fromisoformat(fecha_limite)
                payload["fecha_limite"] = dt.isoformat()
            except Exception:
                st.warning("Fecha inválida; se ignorará. Use formato ISO.")
        try:
            endpoint = "/api/actions/task_from_email" if "Mail" in fuente else "/api/actions/task_from_event" if "Calendar" in fuente else "/api/actions/task_from_email"
            r = requests.post(f"{BACKEND_URL}{endpoint}", json=payload)
            st.success(r.json())
        except Exception as e:
            st.error(e)
