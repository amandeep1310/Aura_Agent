import streamlit as st

def feedback_form():

    st.subheader("💬 Feedback")

    feedback = st.text_area(
        "Revision Feedback",
        height=120
    )

    return feedback