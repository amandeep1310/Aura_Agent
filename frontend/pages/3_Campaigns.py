import streamlit as st

from components.sidebar import show_sidebar
from utils.styles import load_css

load_css()
show_sidebar()

st.title("📁 Campaigns")

if "campaigns" not in st.session_state:

    st.session_state.campaigns = []

campaign_name = st.text_input(
    "Campaign Topic"
)

if st.button(
    "Create Campaign"
):

    if campaign_name:

        st.session_state.campaigns.append(
            {
                "topic": campaign_name
            }
        )

        st.success(
            "Campaign Created"
        )

st.divider()

for campaign in st.session_state.campaigns:

    st.markdown("---")

    st.subheader(
        campaign["topic"]
    )