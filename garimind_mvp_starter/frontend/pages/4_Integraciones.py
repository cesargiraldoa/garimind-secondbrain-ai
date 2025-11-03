import streamlit as st, requests, os, pandas as pd
from dotenv import load_dotenv
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Integraciones", layout="wide")
st.title("🔌 Integraciones: Google & Microsoft")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Google (Drive + Calendar)")
    if st.button("Conectar Google"):
        try:
            r = requests.get(f"{BACKEND_URL}/api/google/auth-url").json()
            st.markdown(f"[Abrir autorización de Google]({r['auth_url']})")
        except Exception as e:
            st.error(e)
    st.caption("Archivos recientes (Drive)")
    if st.button("Ver recientes de Drive"):
        try:
            data = requests.get(f"{BACKEND_URL}/api/google/drive/recent").json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)
    st.caption("Eventos de hoy (Google Calendar)")
    if st.button("Ver hoy (Google)"):
        try:
            events = requests.get(f"{BACKEND_URL}/api/google/calendar/today").json()
            st.dataframe(pd.DataFrame(events))
        except Exception as e:
            st.error(e)

with col2:
    st.subheader("Microsoft (Outlook Calendar)")
    if st.button("Conectar Microsoft"):
        try:
            r = requests.get(f"{BACKEND_URL}/api/ms/auth-url").json()
            st.markdown(f"[Abrir autorización de Microsoft]({r['auth_url']})")
        except Exception as e:
            st.error(e)
    st.caption("Eventos de hoy (Outlook)")
    if st.button("Ver hoy (Outlook)"):
        try:
            data = requests.get(f"{BACKEND_URL}/api/ms/calendar/today").json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)
