import streamlit as st
import os


def show_sidebar():

    image_path = os.path.join(
        os.path.dirname(__file__), "..", "assets", "aura_logo.jpeg"
    )

    st.sidebar.image(image_path, width="stretch")

    st.sidebar.markdown("# Agent AURA")

    st.sidebar.caption("Agent AURA is an AI-powered content generation platform that helps create engaging and impactful content for the AURA Community")

    st.sidebar.markdown("---")

    if st.sidebar.button("Generate", key="nav_generate"):
        st.switch_page("pages/1_Generate.py")

    if st.sidebar.button("History", key="nav_history"):
        st.switch_page("pages/2_History.py")

    if st.sidebar.button("Campaigns", key="nav_campaigns"):
        st.switch_page("pages/3_Campaigns.py")

    if st.sidebar.button("Settings", key="nav_settings"):
        st.switch_page("pages/settings.py")
