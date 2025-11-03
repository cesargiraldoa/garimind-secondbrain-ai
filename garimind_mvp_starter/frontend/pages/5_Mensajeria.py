import streamlit as st, requests, os, pandas as pd
from dotenv import load_dotenv
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Mensajería", layout="wide")
st.title("📬 Mensajería unificada (Gmail + Outlook)")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Gmail")
    max_g = st.number_input("Cantidad (Gmail)", min_value=1, max_value=200, value=50, step=5)
    c1, c2 = st.columns(2)
    if c1.button("Gmail: Inbox"):
        try:
            data = requests.get(f"{BACKEND_URL}/api/google/gmail/inbox", params={"max_results": int(max_g)}).json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)
    if c2.button("Gmail: No leídos"):
        try:
            data = requests.get(f"{BACKEND_URL}/api/google/gmail/unread", params={"max_results": int(max_g)}).json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)

with col2:
    st.subheader("Outlook")
    max_o = st.number_input("Cantidad (Outlook)", min_value=1, max_value=1000, value=50, step=5, key="olmax")
    c3, c4 = st.columns(2)
    if c3.button("Outlook: Inbox"):
        try:
            data = requests.get(f"{BACKEND_URL}/api/ms/mail/inbox", params={"top": int(max_o)}).json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)
    if c4.button("Outlook: No leídos"):
        try:
            data = requests.get(f"{BACKEND_URL}/api/ms/mail/unread", params={"top": int(max_o)}).json()
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(e)
