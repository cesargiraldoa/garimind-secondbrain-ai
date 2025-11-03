import streamlit as st, os, requests
from dotenv import load_dotenv; load_dotenv()
BACKEND = os.getenv("BACKEND_URL","http://localhost:8000")

st.set_page_config(page_title="Gari • Chat", layout="wide")
st.title("💬 Gari • Motor de Razonamiento")

if "hist" not in st.session_state: st.session_state.hist = []

user = st.text_input("Pídele algo a Gari (ej: 'Revisa mi día y sugiere 3 tareas críticas')")
if st.button("Enviar"):
    try:
        r = requests.post(f"{BACKEND}/api/ai/reason", json={"prompt": user}, timeout=120)
        ans = r.json()
        st.session_state.hist.append(("tú", user))
        st.session_state.hist.append(("gari", ans.get("answer","(sin texto)")))
    except Exception as e:
        st.error(e)

for who, msg in st.session_state.hist:
    st.markdown(f"**{who}:** {msg}")
