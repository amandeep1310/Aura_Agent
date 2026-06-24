import streamlit as st

def initialize_session():

    if "generation" not in st.session_state:
        st.session_state.generation = None

    if "feedback" not in st.session_state:
        st.session_state.feedback = ""

    if "history" not in st.session_state:
        st.session_state.history = []