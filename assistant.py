import os
import time
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
import tempfile
import requests
import whisper

# Import chat-related helper functions
from chat.response import get_response, pretty_print
from chat.runs import wait_on_run
from chat.threads import create_thread_and_run, continue_thread_and_run
from chat.tts import openai_transcribe_audio

# ========= Constants and Initialization =========
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_KEY")
VOICE_TTS = "Ava (Premium)"      # Voice name for TTS output
USE_LOCAL_MIC = True            # Toggle between backend mic vs. front-end input
client = OpenAI(api_key=API_KEY)  # Initialize OpenAI client


def send_message_to_server(role: str, content: str):
    url = "http://127.0.0.1:5500/message"
    data = {"role": role, "content": content}
    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            print("Error: Received non-200 status code")
            return
        # JSON 파싱 시도
        try:
            json_data = response.json()
            print("Server response:", json_data)
        except Exception as json_err:
            print("Error parsing JSON response:", json_err)
            print("Raw response text:", response.text)
    except Exception as e:
        print("Error sending message:", e)


def send_wav_file_to_server(file_path):
    url = "http://127.0.0.1:5500/upload_audio"
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files)
            print("Audio file upload response:", response.text)
    except Exception as e:
        print("Error uploading audio file:", e)


def generate_tts_aiff(voice, text, output_path):
    """
    Generate an AIFF file using the macOS 'say' command.
    """
    cmd = f'say -v "{voice}" -o "{output_path}" "{text}"'
    os.system(cmd)


def convert_aiff_to_wav(aiff_path, wav_path):
    """
    Convert AIFF to WAV using the macOS afconvert tool.
    """
    cmd = f'afconvert -f WAVE -d LEI16 "{aiff_path}" "{wav_path}"'
    subprocess.run(cmd, shell=True, check=True)


def wait_for_audio_finished():
    # Poll the server every 1 second until it indicates that audio playback is complete.
    while True:
        try:
            response = requests.get("http://127.0.0.1:5500/audio_finished")
            if response.status_code == 200:
                data = response.json()
                if data.get("audio_finished", False):
                    print("[Assistant] Audio finished signal received.")
                    break
        except Exception as e:
            print("[Assistant] Error polling audio finished status:", e)
        time.sleep(1)


def assistant_process(shared_queue):

    """Main loop for the AI assistant process."""
    print("[Assistant] Starting assistant process...")

    name_to_thread = {}        # Map person name to their conversation thread
    current_name = None

    recognizer = sr.Recognizer()
    mic = None
    model = whisper.load_model("base.en")

    if USE_LOCAL_MIC:
        mic = sr.Microphone()
        # Calibrate once for ambient noise to improve recognition speed
        """with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Assistant] Microphone calibrated for ambient noise.")"""

    while True:
        try:
            # Check if a new face (name) is recognized
            new_name = ""
            if not current_name or not shared_queue.empty():
                # Get a new recognized name from the vision process (if available)
                new_name = shared_queue.get().strip()

            # If a new person is detected (or person changed)
            if new_name != "" and new_name != current_name:
                if current_name:
                    print(f"[Assistant] Switching conversation to {new_name}")
                current_name = new_name

                # If this is a first-time visitor or a "Guest", start a new thread
                if current_name not in name_to_thread:
                    # Create a greeting message as if the user introduced themselves
                    initial_user_msg = (
                        f"Hi, my name is {current_name}"
                        # if current_name != "Guest" else "Hello, I am a visitor."
                    )
                    thread, run = create_thread_and_run(client, ASSISTANT_ID, initial_user_msg)
                    wait_on_run(client, run, thread)
                    # Get assistant's greeting response
                    response_message = get_response(client, thread)
                    # Format and send the assistant's response (text and audio) to UI
                    ui_message = pretty_print(VOICE_TTS, response_message)
                    print(f"[Assistant] {ui_message}")
                        
                    # Save the new thread for this person
                    name_to_thread[current_name] = thread

                    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_aiff:
                        aiff_path = tmp_aiff.name
                    generate_tts_aiff(VOICE_TTS, ui_message, aiff_path)

                    # 2. Convert the AIFF to WAV format
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                        wav_path = tmp_wav.name
                    convert_aiff_to_wav(aiff_path, wav_path)
                    
                    send_wav_file_to_server(wav_path)

                    send_message_to_server("assistant", ui_message)

                else:
                    # Resume existing conversation thread for returning person
                    print(f"[Assistant] Resuming conversation with {current_name}")
                    thread = name_to_thread[current_name]
                    send_message_to_server("system", "Listening...")

            wait_for_audio_finished()
            send_message_to_server("system", "Listening...")

            # Listen for the user's speech input
            user_message = ""
            if USE_LOCAL_MIC:
                # Use backend microphone for voice input (if enabled)
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio_data = recognizer.listen(source, timeout=3)
                with open("temp.wav", "wb") as f:
                    f.write(audio_data.get_wav_data())
                send_message_to_server("system", "Transcribing...")
                print("[Assistant] Transcribing speech...")
                try:
                    result = model.transcribe("temp.wav")
                    # result = openai_transcribe_audio(client, audio_data)
                except Exception as e:
                    print(f"[Assistant] Transcription error: {e}")
                    continue  # Skip to next loop iteration
                user_message = result["text"].strip()
            else:
                # Use message from front-end (if provided via WebSocket)
                pass
            if not user_message:
                # No speech detected or transcription empty
                print("[Assistant] No user message detected (silence or error).")
                continue

            print(f"User said: {user_message}")
            send_message_to_server("user", user_message)
            time.sleep(1)
            send_message_to_server("system", "Processing...")

            # Continue the conversation on the appropriate thread
            if current_name:
                if current_name not in name_to_thread:
                    # Safety check: create a new thread if none exists (should not normally happen)
                    thread, run = create_thread_and_run(client, ASSISTANT_ID, user_message)
                    name_to_thread[current_name] = thread
                else:
                    thread = name_to_thread[current_name]
                    run = continue_thread_and_run(client, ASSISTANT_ID, thread, user_message)
                # Wait for the assistant's answer and retrieve it
                wait_on_run(client, run, thread)
                response = get_response(client, thread)
                # Output the assistant's response (speak it and send to UI)
                ui_message = pretty_print(VOICE_TTS, response)
                print(f"[Assistant] {ui_message}")
                if ui_message:
                    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_aiff:
                        aiff_path = tmp_aiff.name
                    generate_tts_aiff(VOICE_TTS, ui_message, aiff_path)

                    # 2. Convert the AIFF to WAV format
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                        wav_path = tmp_wav.name
                    convert_aiff_to_wav(aiff_path, wav_path)
                    
                    send_wav_file_to_server(wav_path)
                    send_message_to_server("assistant", ui_message)

        except sr.WaitTimeoutError:
            # No speech heard within the timeout
            print("[Assistant] Listening timed out. Waiting for user to speak...")
            response = requests.post("http://127.0.0.1:5500/audio_finished")
            continue
        except Exception as e:
            # Catch-all for any unexpected errors to prevent crash
            print(f"[Assistant] Error in assistant loop: {e}")
            continue
