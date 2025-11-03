import streamlit as st, requests, os, pandas as pd
from dotenv import load_dotenv
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Memoria & Tareas", layout="wide")
st.title("📚 Memoria & ✅ Tareas")

tab1, tab2 = st.tabs(["Recuerdos", "Tareas"])

with tab1:
    c1, c2, c3 = st.columns(3)
    q = c1.text_input("Buscar", "")
    tag = c2.text_input("Tag", "")
    proyecto_id = c3.number_input("Proyecto ID", min_value=0, step=1)
    if st.button("Buscar"):
        params = {}
        if q: params["q"] = q
        if tag: params["tag"] = tag
        if proyecto_id: params["proyecto_id"] = int(proyecto_id)
        try:
            data = requests.get(f"{BACKEND_URL}/api/recuerdos", params=params).json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)

with tab2:
    c1, c2 = st.columns([3,1])
    titulo = c1.text_input("Nueva tarea")
    proyecto_id_t = c2.number_input("Proyecto ID", min_value=0, step=1, key="pidt")
    if st.button("Crear tarea"):
        try:
            payload = {"titulo": titulo}
            if proyecto_id_t: payload["proyecto_id"] = int(proyecto_id_t)
            r = requests.post(f"{BACKEND_URL}/api/tareas", json=payload)
            st.success(r.json())
        except Exception as e:
            st.error(e)

    st.subheader("Listado")
    params = {}
    if proyecto_id_t: params["proyecto_id"] = int(proyecto_id_t)
    try:
        data = requests.get(f"{BACKEND_URL}/api/tareas", params=params).json()
        st.dataframe(pd.DataFrame(data))
    except Exception as e:
        st.error(e)
