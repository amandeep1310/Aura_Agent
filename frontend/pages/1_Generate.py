import streamlit as st
from services.api import generate_content, get_campaign

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

import time

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

objective = st.text_input(
    "Campaign Objective"
)

if st.button("Generate Content"):

    if topic.strip() == "" or objective.strip() == "":

        st.warning(
            "Please enter topic and objective"
        )

    else:

        with st.spinner("Generating Campaign..."):

            response = generate_content(
                topic,
                objective
            )

if "error" in response:

    st.error(response["error"])

else:

    campaign_id = response["campaign_id"]

    time.sleep(5)

    campaign_data = get_campaign(
        campaign_id
    )

    st.write(campaign_data)

    st.session_state.generation = campaign_data

    st.session_state.history.append(
        campaign_data
    )

    log_info(
        f"Generated Topic: {topic}"
    )

    st.success(
        "Campaign Generated Successfully"
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