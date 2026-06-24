import streamlit as st

from components.sidebar import show_sidebar
from utils.styles import load_css

load_css()
show_sidebar()

st.title("⚙ Settings")

st.subheader("Application Information")

st.info(
    """
    Agent AURA

    Version: 1.0

    Frontend: Streamlit

    Backend: FastAPI (Upcoming)

    Database: PostgreSQL (Upcoming)
    """
)

st.divider()

st.subheader("Data Management")

# Clear History

if st.button(
    "Clear History"
):

    st.session_state.history = []

    st.success(
        "History Cleared"
    )

# Clear Campaigns

if st.button(
    "Clear Campaigns"
):

    st.session_state.campaigns = []

    st.success(
        "Campaigns Cleared"
    )

# Clear Feedback

if st.button(
    "Clear Feedback"
):

    if "feedback" in st.session_state:

        st.session_state.feedback = ""

    st.success(
        "Feedback Cleared"
    )