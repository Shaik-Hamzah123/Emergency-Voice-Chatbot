import tempfile
import re  # This can be removed if not used
from io import BytesIO
from pydub import AudioSegment
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from utils import *


st.title(":blue[Emergency Help Bot] 🚨🚑🆘")
st.sidebar.image('./emergency.jpg', use_column_width=True)

# Initialize session states if not already present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = []
if "played_audios" not in st.session_state:
    st.session_state.played_audios = {}

# Handle the initial chat history setup
if len(st.session_state.chat_history) == 0:
    welcome_audio_path = create_welcome_message()
    st.session_state.chat_history = [
        AIMessage(content="Hello, you’ve reached the Emergency Help Desk. Please let me know if it's a medical, fire, police, or mental health emergency—I'm here to guide you right away.", audio_file=welcome_audio_path)
    ]
    st.session_state.played_audios[welcome_audio_path] = False

# Sidebar with mic button
with st.sidebar:
    audio_bytes = audio_recorder(
        energy_threshold=0.01,
        pause_threshold=0.8,
        text="Speak on clicking the ICON (Max 5 min) \n",
        recording_color="#e9b61d",   # yellow
        neutral_color="#2abf37",    # green
        icon_name="microphone",
        icon_size="2x"
    )

    if audio_bytes:
        temp_audio_path = audio_bytes_to_wav(audio_bytes)
        if temp_audio_path:
            try:
                user_input = speech_to_text(audio_bytes)
                if user_input:
                    st.session_state.chat_history.append(HumanMessage(content=user_input, audio_file=temp_audio_path))
                    
                    response = get_llm_response(user_input, st.session_state.chat_history)
                    
                    audio_response = text_to_speech(response)
                    audio_stream = BytesIO()
                    audio_response.export(audio_stream, format="mp3")
                    audio_stream.seek(0)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_response:
                        temp_audio_response.write(audio_stream.read())
                        audio_response_file_path = temp_audio_response.name

                    st.session_state.chat_history.append(AIMessage(content=response, audio_file=audio_response_file_path))
                    st.session_state.played_audios[audio_response_file_path] = False
                else:
                    st.error("Sorry, I couldn't understand your speech. Please try again.")
            except Exception as e:
                st.error(f"An error occurred during speech transcription: {str(e)}")

    if st.button("Start New Chat"):
        st.session_state.chat_histories.append(st.session_state.chat_history)
        welcome_audio_path = create_welcome_message()
        st.session_state.chat_history = [
            AIMessage(content="Hello, you’ve reached the Emergency Help Desk. Please let me know if it's a medical, fire, police, or mental health emergency—I'm here to guide you right away.", audio_file=welcome_audio_path)
        ]
        st.session_state.played_audios[welcome_audio_path] = False

# Display chat history in the main area
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            if hasattr(message, 'audio_file'):
                if not st.session_state.played_audios.get(message.audio_file, False):
                    st.audio(message.audio_file, format="audio/mp3")
                    st.session_state.played_audios[message.audio_file] = True
                else:
                    st.audio(message.audio_file, format="audio/mp3")
    elif isinstance(message, HumanMessage):
        with st.chat_message("user"):
            if hasattr(message, 'audio_file'):
                st.audio(message.audio_file, format="audio/wav")