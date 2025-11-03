import streamlit as st, requests, os, pandas as pd
from dotenv import load_dotenv
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Proyectos", layout="wide")
st.title("🗂️ Proyectos")

with st.form("crear_proyecto"):
    nombre = st.text_input("Nombre del proyecto")
    objetivo = st.text_area("Objetivo (opcional)")
    submitted = st.form_submit_button("Crear proyecto + carpeta")
    if submitted and nombre.strip():
        try:
            r = requests.post(f"{BACKEND_URL}/api/projects", json={"nombre": nombre, "objetivo": objetivo})
            st.success(f"Creado: {r.json()}")
        except Exception as e:
            st.error(e)

st.subheader("Proyectos existentes")
try:
    data = requests.get(f"{BACKEND_URL}/api/projects").json()
    st.dataframe(pd.DataFrame(data))
    st.info("Las carpetas se crean en el servidor en `data/projects/<slug>`.")
except Exception as e:
    st.error(e)
