import openai
import time
from openai import OpenAI
import whisper
from pydub import AudioSegment
import os
import speech_recognition as sr
from dotenv import load_dotenv

# ========= Constants =========
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_KEY")

VOICE_TTS = "Ava (Premium)"  # e.g., "Samantha", "Ava (Premium)"
ONLY_TEXT = True  # Set to True for text-only interaction

# ========= Initialize OpenAI Client =========
client = OpenAI(api_key=API_KEY)


# ========= Thread and Message Helpers =========
def submit_message(assistant_id: str, thread, user_message: str):
    """
    Submits a user message to the specified thread and starts a run.
    Returns the newly created run.
    """
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )


def create_thread_and_run(user_input: str):
    """
    Creates a new thread, submits the user message, and returns (thread, run).
    """
    thread = client.beta.threads.create()
    run = submit_message(ASSISTANT_ID, thread, user_input)
    return thread, run


def continue_thread_and_run(thread, user_input: str):
    """
    Submits a user message to an existing thread and returns the run.
    """
    return submit_message(ASSISTANT_ID, thread, user_input)


def wait_on_run(run, thread):
    """
    Polls run status until it is no longer 'queued' or 'in_progress'.
    """
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            print("Run failed:", run_status.last_error)
            break
        time.sleep(2)


def get_response(thread):
    """
    Returns the full list of messages (in ascending order) from the thread.
    """
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")


def pretty_print(messages, enable_tts: bool = False):
    """
    Prints the last assistant message. If enable_tts is True,
    uses macOS 'say' command for TTS (adjust if on another OS).
    """
    if not messages:
        return
    messages_list = list(messages)
    last_message = messages_list[-1]
    role = last_message.role
    content = last_message.content[0].text.value

    print(f"{role}: {content}")

    if enable_tts and role == "assistant":
        os.system(f'say -v "{VOICE_TTS}" "{content}"')


# ========= Audio Helpers =========
def milliseconds_until_sound(sound, silence_threshold_in_decibels=-30.0, chunk_size=10) -> int:
    """
    Returns the number of milliseconds until sound above the threshold is detected.
    """
    trim_ms = 0  # in milliseconds
    # to avoid infinite loop, ensure chunk_size > 0
    assert chunk_size > 0, "Chunk size must be positive."

    while trim_ms < len(sound):
        segment = sound[trim_ms: trim_ms + chunk_size]
        if segment.dBFS >= silence_threshold_in_decibels:
            break
        trim_ms += chunk_size

    return trim_ms


def openai_transcribe_audio(filepath: str) -> str:
    """
    Trims leading silence from the audio at `filepath` and
    transcribes the result using OpenAI's Whisper.
    """
    audio = AudioSegment.from_file(filepath)
    start_trim = milliseconds_until_sound(audio)
    trimmed = audio[start_trim:]
    trimmed.export("/tmp/trimmed.wav", format="wav")

    with open("/tmp/trimmed.wav", "rb") as audio_data:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data
        )
    return transcription.text


# ========= Main Logic =========
def main():
    new_thread = True
    thread = None

    if ONLY_TEXT:
        # Text-only loop
        while True:
            message = input("Type Your Message: ")
            if not message.strip():
                continue

            if new_thread:
                thread, run = create_thread_and_run(message)
                new_thread = False
            else:
                run = continue_thread_and_run(thread, message)

            wait_on_run(run, thread)
            pretty_print(get_response(thread))

    else:
        # Speech loop
        model = whisper.load_model("base.en")
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        while True:
            try:
                print("Listening...")
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio_data = recognizer.listen(source, timeout=5)

                # Save audio to file
                with open("temp.wav", "wb") as f:
                    f.write(audio_data.get_wav_data())

                # Transcribe using local Whisper model (faster on GPU) or OpenAI's API
                print("Transcribing...")
                result = model.transcribe("temp.wav")
                message = result["text"].strip()

                if not message:
                    print("Nothing said...")
                    continue

                print(f"You said: {message}")

                if new_thread:
                    thread, run = create_thread_and_run(message)
                    new_thread = False
                else:
                    run = continue_thread_and_run(thread, message)

                wait_on_run(run, thread)
                pretty_print(get_response(thread), enable_tts=True)

            except sr.WaitTimeoutError:
                print("Listening timed out. Try speaking again.")
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
