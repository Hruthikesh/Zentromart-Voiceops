
"""Run with: python -m streamlit run app.py"""

import tempfile
import hashlib
from pathlib import Path

import streamlit as st

from src.factory import make_agent
from src.voice import Voice


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ZentroMart Support",
    page_icon="🎧",
    layout="wide"
)

st.title("ZentroMart Support")
st.caption("VoiceOps Capstone · Fictional store · Synthetic orders only")

st.info(
    "You are talking to an AI assistant. "
    "Ask about delivery, returns, refunds or an order."
)


# --------------------------------------------------
# SESSION MANAGEMENT
# --------------------------------------------------

if st.sidebar.button("Start a new conversation"):
    st.session_state.clear()
    st.rerun()


# --------------------------------------------------
# INITIALIZE AGENT
# --------------------------------------------------

try:
    if "agent" not in st.session_state:
        with st.spinner("Loading the policy index..."):
            st.session_state.agent = make_agent()
            st.session_state.messages = []

except Exception as exc:
    st.error("The assistant could not initialize.")
    st.caption('Check local settings and connectivity. Private error details are not displayed.')
    st.stop()


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------------------------
# VOICE INPUT
# --------------------------------------------------

audio = st.audio_input("Record a question")

text = st.chat_input("Type your question")

if audio is not None:
    digest = hashlib.sha256(audio.getvalue()).hexdigest()

    if digest != st.session_state.get("last_audio"):

        st.session_state.last_audio = digest

        try:
            with tempfile.TemporaryDirectory() as folder:

                path = Path(folder) / "question.wav"
                path.write_bytes(audio.getvalue())

                with st.spinner("Transcribing your voice..."):
                    text = Voice().transcribe(path)

        except Exception as exc:
            st.error("Audio transcription failed.")
            st.caption('Check your Gnani account and connection, then record again.')


# --------------------------------------------------
# PROCESS USER QUESTION
# --------------------------------------------------

if text is not None:

    from src.tools import redact

    # Display user question
    safe_text = redact(text)

    st.session_state.messages.append({
        "role": "user",
        "content": safe_text
    })

    with st.chat_message("user"):
        st.write(safe_text)

    # Get assistant response
    try:
        with st.spinner("Checking policies and preparing your answer..."):

            result = st.session_state.agent.respond(text)

        reply = result["reply"]

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply
        })

        # Display assistant response
        with st.chat_message("assistant"):

            st.write(reply)

            # --------------------------------------------------
            # TEXT-TO-SPEECH
            # --------------------------------------------------

            try:
                with tempfile.TemporaryDirectory() as folder:

                    path = Path(folder) / "reply.wav"

                    with st.spinner("Generating voice response..."):
                        Voice().speak(reply, path)

                    st.audio(
                        path.read_bytes(),
                        format="audio/wav"
                    )

            except Exception as exc:
                st.warning(
                    "Text reply is available, but voice generation failed."
                )
                st.caption('Check your Gnani quota and voice settings.')

            # --------------------------------------------------
            # SOURCES USED
            # --------------------------------------------------

            with st.expander("Sources used"):

                for chunk in result.get("retrieved_chunks", []):

                    if chunk["id"] in result.get("sources", []):

                        st.markdown(
                            f"**{chunk['id']} · {chunk['file']}**"
                        )

                        st.write(chunk["text"])

    except Exception as exc:

        st.error("The assistant could not finish this request.")

        # Display actual error for debugging
        st.caption('Check quota and settings. Retry the same question or start a new conversation.')
