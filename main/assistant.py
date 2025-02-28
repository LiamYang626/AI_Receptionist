from openai import OpenAI
import os
import subprocess
import tempfile
import time
import speech_recognition as sr
from dotenv import load_dotenv
from chat.response import get_response
from chat.runs import wait_on_run
from chat.threads import create_thread_and_run, continue_thread_and_run
from chat.tts import openai_transcribe_audio

# ========= Constants =========
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_KEY")
VOICE_TTS = "Ava (Premium)"  # e.g., "Samantha", "Ava (Premium)"
ONLY_TEXT = False  # Set to True for text-only interaction

# ========= Initialize OpenAI Client =========
client = OpenAI(api_key=API_KEY)

# ========= Global Log Capture =========
output_logs = []  # Global list to capture printed output
import builtins
original_print = print
def new_print(*args, **kwargs):
    message = " ".join(str(arg) for arg in args)
    output_logs.append(message)
    original_print(*args, **kwargs)
print = new_print


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


def pretty_print(voice_tts, message, enable_tts: bool = False):
    """
    Prints the last assistant message. If enable_tts is True,
    uses macOS 'say' command for TTS (adjust if on another OS).
    """
    if not message:
        return
    role = message.role
    content = message.content[0].text.value

    print(f"{role}: {content}")

    '''
    if enable_tts and role == "assistant":
        os.system(f'say -v "{voice_tts}" "{content}"')
    '''
    return content


def wait_for_tts_finish(speaking_flag):
    """Wait until speaking_flag is reset to False."""
    while speaking_flag.value:
        time.sleep(0.1)


# ========= Main Logic =========
def assistant_process(shared_queue, message_queue, signal_queue, viz_queue, speaking_flag):
    print("[Assistant] Starting assistant process...")

    # new_thread= True
    # thread = None

    name_to_thread = {}
    current_name = None

    if ONLY_TEXT:
        # Text-only loop
        while True:
            new_name = ""
            if not current_name or not shared_queue.empty():
                new_name = shared_queue.get().strip()

            if new_name != "" and new_name != current_name:
                if current_name:
                    print(f"Switching conversation to new recognized person: {new_name}")
                current_name = new_name

                if current_name not in name_to_thread:
                    thread, run = create_thread_and_run(client, ASSISTANT_ID, f"Hi, my name is {current_name}")
                    wait_on_run(client, run, thread)
                    pretty_print(VOICE_TTS, get_response(client, thread))
                    name_to_thread[current_name] = thread
                else:
                    print(f"Resuming conversation with {current_name}")

            # Notify that the assistant is ready for input.
            signal_queue.put("received")

            user_message = message_queue.get().strip()

            if not user_message:
                continue

            # Continue the conversation with the current active thread.
            if current_name:
                if current_name not in name_to_thread:
                    # Safety check (should rarely happen)
                    thread, run = create_thread_and_run(client, ASSISTANT_ID, user_message)
                    name_to_thread[current_name] = thread
                else:
                    thread = name_to_thread[current_name]
                    run = continue_thread_and_run(client, ASSISTANT_ID, thread, user_message)
                wait_on_run(client, run, thread)
                pretty_print(VOICE_TTS, get_response(client, thread))

            # ========= Unused code for now =========
            # ========= Code for guests (Unrecognized people) =========
            '''
            if new_thread:
                thread, run = create_thread_and_run(user_message)
                new_thread = False
            else:
                run = continue_thread_and_run(thread, user_message)

            wait_on_run(run, thread)
            pretty_print(get_response(thread))
            '''
    else:
        # Speech loop
        # model = whisper.load_model("base.en")
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        while True:
            try:
                new_name = ""
                if not current_name or not shared_queue.empty():
                    new_name = shared_queue.get().strip()

                if new_name != "" and new_name != current_name:
                    if current_name:
                        print(f"Switching conversation to new recognized person: {new_name}")
                    current_name = new_name

                    if current_name not in name_to_thread:
                        signal_queue.put("Initializing...")
                        thread, run = create_thread_and_run(client, ASSISTANT_ID, f"Hi, my name is {current_name}")
                        wait_on_run(client, run, thread)
                        message = pretty_print(VOICE_TTS, get_response(client, thread), enable_tts=True)
                        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_aiff:
                            aiff_path = tmp_aiff.name
                        generate_tts_aiff(VOICE_TTS, message, aiff_path)

                        # 2. Convert the AIFF to WAV format
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                            wav_path = tmp_wav.name
                        convert_aiff_to_wav(aiff_path, wav_path)
                        viz_queue.put((wav_path, message))
                        name_to_thread[current_name] = thread
                    else:
                        print(f"Resuming conversation with {current_name}")

                print("Listening...")
                signal_queue.put("Listening...")
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio_data = recognizer.listen(source, timeout=5)

                # Save audio to file
                with open("temp.wav", "wb") as f:
                    f.write(audio_data.get_wav_data())

                # Transcribe using local Whisper model (faster on GPU) or OpenAI's API
                print("Transcribing...")
                result = openai_transcribe_audio(client, "./temp.wav")
                user_message = result
                '''
                result = model.transcribe("temp_mic.wav")
                user_message = result["text"].strip()
                '''

                if not user_message:
                    print("Nothing said...")
                    continue

                print(f"You said: {user_message}")
                signal_queue.put("Processing...")

                # Continue the conversation with the current active thread.
                if current_name:
                    if current_name not in name_to_thread:
                        # Safety check (should rarely happen)
                        thread, run = create_thread_and_run(client, ASSISTANT_ID, user_message)
                        name_to_thread[current_name] = thread
                    else:
                        thread = name_to_thread[current_name]
                        run = continue_thread_and_run(client, ASSISTANT_ID, thread, user_message)
                    wait_on_run(client, run, thread)
                    message = pretty_print(VOICE_TTS, get_response(client, thread), enable_tts=True)
                    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_aiff:
                        aiff_path = tmp_aiff.name
                    generate_tts_aiff(VOICE_TTS, message, aiff_path)

                    # 2. Convert the AIFF to WAV format
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                        wav_path = tmp_wav.name
                    convert_aiff_to_wav(aiff_path, wav_path)
                    speaking_flag.value = True
                    viz_queue.put((wav_path, message))
                    wait_for_tts_finish(speaking_flag)

                    # ========= Unused code for now =========
                    # ========= Code for guests (Unrecognized people) =========
                    '''
                    if new_thread:
                        thread, run = create_thread_and_run(user_message)
                        new_thread = False
                    else:
                        run = continue_thread_and_run(thread, user_message)
            
                    wait_on_run(run, thread)
                    pretty_print(get_response(thread), enable_tts=True)
                    '''

            except sr.WaitTimeoutError:
                print("Listening timed out. Try speaking again.")
            except Exception as e:
                print(f"An error occurred: {e}")
