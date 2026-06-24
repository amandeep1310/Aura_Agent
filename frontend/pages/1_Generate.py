import streamlit as st

st.set_page_config(
    page_title="Agent AURA",
    layout="wide"
)

from components.sidebar import show_sidebar
from utils.styles import load_css

from components.poster_viewer import show_poster
from components.poster_content import show_poster_content
from components.poll_viewer import show_poll
from components.feedback_form import feedback_form
from components.revision_plan import show_revision_plan

from utils.session import initialize_session
from utils.logger import log_info

load_css()
show_sidebar()

initialize_session()

st.title("🤖 Agent AURA")

st.subheader(
    "Creating content for Aura community."
)

topic = st.text_input(
    "Campaign Topic"
)

if st.button(
    "Generate Content"
):

    if topic.strip() == "":

        st.warning(
            "Please enter a topic"
        )

    else:

        generation_data = {
            "topic": topic
        }

        st.session_state.generation = generation_data

        st.session_state.history.append(
            generation_data
        )

        log_info(
            f"Generated Topic: {topic}"
        )

        st.success(
            "Generation Completed"
        )

if st.session_state.generation:

    st.divider()

    show_poster()

    st.divider()

    show_poster_content()

    st.divider()

    show_poll()

    st.divider()

    feedback = feedback_form()

    if st.button(
        "Generate Revision Plan"
    ):

        if feedback.strip() == "":

            st.warning(
                "Please enter feedback"
            )

        else:

            st.session_state.feedback = feedback

            log_info(
                f"Feedback Submitted: {feedback}"
            )

            st.divider()

            show_revision_plan(
                feedback
            )