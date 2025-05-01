import time
import requests
import tempfile
import re
from io import BytesIO
from gtts import gTTS
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from pydub import AudioSegment
from groq import Groq
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

tts_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Initialize the Groq model for LLM responses
llm = ChatGroq(model="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"), max_tokens=500)
# llm = ChatOpenAI(
#     model_name="gpt-4.1-mini",
#     openai_api_key=os.getenv("COMET_API_KEY"),
#     openai_api_base="https://api.cometapi.com/v1"
# )

# Set the path to ffmpeg executable
AudioSegment.converter = "/bin/ffmpeg"

def audio_bytes_to_wav(audio_bytes):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            audio = AudioSegment.from_file(BytesIO(audio_bytes))
            # Downsample to reduce file size if needed
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(temp_wav.name, format="wav")
            return temp_wav.name
    except Exception as e:
        st.error(f"Error during WAV file conversion: {e}")
        return None

def split_audio(file_path, chunk_length_ms):
    audio = AudioSegment.from_wav(file_path)
    return [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

def speech_to_text(audio_bytes):
    try:
        # Convert the audio bytes to WAV
        temp_wav_path = audio_bytes_to_wav(audio_bytes)

        if temp_wav_path is None:
            return "Error"

        # Increase file size limit
        if os.path.getsize(temp_wav_path) > 50 * 1024 * 1024:
            st.error("File size exceeds the 50 MB limit. Please upload a smaller file.")
            return "Error"

        # Define chunk length (e.g., 5 minutes = 5 * 60 * 1000 milliseconds)
        chunk_length_ms = 5 * 60 * 1000
        chunks = split_audio(temp_wav_path, chunk_length_ms)

        transcription = ""
        for chunk in chunks:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_chunk:
                chunk.export(temp_chunk.name, format="wav")
                with open(temp_chunk.name, "rb") as file:
                    chunk_transcription = client.audio.transcriptions.create(
                        file=("audio.wav", file.read()),
                        model="whisper-large-v3",
                        response_format="text",
                        language="en",
                        temperature=0.0,
                    )
                    transcription += chunk_transcription + " "

        return transcription.strip()
    except Exception as e:
        st.error(f"Error during speech-to-text conversion: {e}")
        return "Error"

def text_to_speech(text: str, retries: int = 3, delay: int = 5) -> AudioSegment:
    """
    Convert text to speech using ElevenLabs API with retry logic.

    Args:
        text (str): Text to convert.
        retries (int): Number of retry attempts on connection errors.
        delay (int): Delay in seconds between retries.

    Returns:
        AudioSegment: Generated speech audio. Returns 1 second of silence on failure.
    """
    attempt = 0
    while attempt < retries:
        try:
            # Request speech synthesis (streaming generator)
            response_stream = tts_client.text_to_speech.convert(
                text=text,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            # Write streamed bytes to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                for chunk in response_stream:
                    f.write(chunk)
                temp_path = f.name

            # Load and return the audio
            audio = AudioSegment.from_mp3(temp_path)
            return audio

        except requests.ConnectionError:
            attempt += 1
            if attempt < retries:
                st.warning(f"Internet connection issue. Retrying ({attempt}/{retries})...")
                time.sleep(delay)
            else:
                st.error(f"Failed to connect after {retries} attempts. Please check your internet connection.")
                return AudioSegment.silent(duration=1000)

        except Exception as e:
            st.error(f"Error during text-to-speech conversion: {e}")
            return AudioSegment.silent(duration=1000)

    return AudioSegment.silent(duration=1000)

def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)

def get_llm_response(query, chat_history):
    try:
        template = template = """
                    You are an experienced Emergency Response Phone Operator trained to handle critical situations in India.
                    Your role is to guide users calmly and clearly during emergencies involving:

                    - Medical crises (injuries, heart attacks, etc.)
                    - Fire incidents
                    - Police/law enforcement assistance
                    - Suicide prevention or mental health crises

                    You must:

                    1. **Remain calm and assertive**, as if speaking on a phone call.
                    2. **Ask for and confirm key details** like location, condition of the person, number of people involved, etc.
                    3. **Provide immediate and practical steps** the user can take before help arrives.
                    4. **Share accurate, India-based emergency helpline numbers** (e.g., 112, 102, 108, 1091, 1098, 9152987821, etc.).
                    5. **Prioritize user safety**, and clearly instruct them what *not* to do as well.
                    6. If the situation involves **suicidal thoughts or mental distress**, respond with compassion and direct them to appropriate mental health helplines and safety actions.

                    If the user's query is not related to an emergency, respond with:
                    "I can only assist with urgent emergency-related issues. Please contact a general support line for non-emergency questions."

                    Use an authoritative, supportive tone, short and direct sentences, and tailor your guidance to **urban and rural Indian contexts**.

                    **Chat History:** {chat_history}

                    **User:** {user_query}
                    """

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm | StrOutputParser()

        response_gen = chain.stream({
            "chat_history": chat_history,
            "user_query": query
        })

        response_text = ''.join(list(response_gen))
        response_text = remove_punctuation(response_text)

        # Remove repeated text
        response_lines = response_text.split('\n')
        unique_lines = list(dict.fromkeys(response_lines))  # Remove duplicates while preserving order
        cleaned_response = '\n'.join(unique_lines)

        return cleaned_response
    except Exception as e:
        st.error(f"Error during LLM response generation: {e}")
        return "Error"

def create_welcome_message() -> str:
    """
    Generate a welcome message audio file for the Emergency Help Desk.

    Returns:
        str: Path to the generated MP3 file (or None on failure).
    """
    welcome_text = (
        "Hello, you’ve reached the Emergency Help Desk. "
        "Please let me know if it's a medical, fire, police, or mental health emergency—"
        "I'm here to guide you right away."
    )

    try:
        # Request speech synthesis (streaming generator)
        response_stream = tts_client.text_to_speech.convert(
            text=welcome_text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        # Save streamed bytes to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            for chunk in response_stream:
                f.write(chunk)
            return f.name

    except requests.ConnectionError:
        st.error("Failed to generate welcome message due to connection error.")
    except Exception as e:
        st.error(f"Error creating welcome message: {e}")

    return None