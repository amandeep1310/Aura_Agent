import streamlit as st

def show_poll():

    st.subheader("📊 Poll")

    st.markdown(
        """
**Question**

Why do organizations need AI inventory?
"""
    )

    st.radio(
        "Select Option",
        [
            "Compliance",
            "Governance",
            "Risk Management",
            "All of the Above"
        ],
        label_visibility="collapsed"
    )