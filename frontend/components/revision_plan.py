import streamlit as st

def show_revision_plan(feedback):

    st.subheader("🔄 Revision Plan")

    revision_plan = {
        "changes": [
            {
                "component": "image_prompt",
                "action": "modify",
                "change": feedback
            }
        ]
    }

    st.json(revision_plan)