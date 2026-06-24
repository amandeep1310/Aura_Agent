import streamlit as st

from components.sidebar import show_sidebar
from utils.styles import load_css

load_css()
show_sidebar()

st.title("📜 History")

if "history" not in st.session_state:

    st.session_state.history = []

if len(st.session_state.history) == 0:

    st.info(
        "No Generations Yet"
    )

else:

    for item in reversed(
        st.session_state.history
    ):

        st.markdown("---")

        st.subheader(
            item["topic"]
        )