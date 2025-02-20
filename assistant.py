from openai import OpenAI
import os
import speech_recognition as sr
import eel
from dotenv import load_dotenv
from chat.response import get_response, pretty_print
from chat.runs import wait_on_run
from chat.threads import create_thread_and_run, continue_thread_and_run
from chat.tts import openai_transcribe_audio
from chat.connect import *

# ========= Constants =========
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_KEY")
VOICE_TTS = "Ava (Premium)"  # e.g., "Samantha", "Ava (Premium)"
VOICE_MODE = True  # Set to True for text-only interaction

# ========= Initialize OpenAI Client =========
client = OpenAI(api_key=API_KEY)


# ========= Main Logic =========
def assistant_process(shared_queue, message_queue, signal_queue, mode_flag):
    print("[Assistant] Starting assistant process...")

    # new_thread= True
    # thread = None

    name_to_thread = {}
    current_name = None

    recognizer = sr.Recognizer()
    mic = sr.Microphone()


    # Text-only loop
    while True:
        VOICE_MODE = (mode_flag.value == 0)
        try:
            new_name = ""
            if not current_name or not shared_queue.empty():
                new_name = shared_queue.get().strip()

            if new_name != "" and new_name != current_name:
                if current_name:
                    if VOICE_MODE:
                        speak(f"Switching conversation to new recognized person: {new_name}")
                    else:
                        eel.receiverText(f"Switching conversation to new recognized person: {new_name}")
                current_name = new_name

                if current_name not in name_to_thread:
                    thread, run = create_thread_and_run(client, ASSISTANT_ID, f"Hi, my name is {current_name}")
                    wait_on_run(client, run, thread)
                    pretty_print(VOICE_TTS, get_response(client, thread), VOICE_MODE)
                    name_to_thread[current_name] = thread
                else:
                    system_message = str(f"Resuming conversation with {current_name}")
                    if VOICE_MODE:
                        speak(system_message)
                    else:
                        display(system_message)


            # Notify that the assistant is ready for input.
            signal_queue.put("received")

            if VOICE_MODE:
                eel.speak("listening....")
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio_data = recognizer.listen(source, timeout=5)

                # Save audio to file
                with open("temp.wav", "wb") as f:
                    f.write(audio_data.get_wav_data())

                # Transcribe using local Whisper model (faster on GPU) or OpenAI's API
                print("Transcribing...")
                eel.DisplayMessage("Transcribing...")
                result = openai_transcribe_audio(client, "./temp.wav")
                user_message = result.strip()

                if not user_message:
                    print("Nothing said...")
                    continue

                print(f"You said: {user_message}")
                speak(user_message)

            else:
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
                response = get_response(client, thread)
                pretty_print(VOICE_TTS, response, VOICE_MODE)
                display_response(response)

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
        except sr.WaitTimeoutError:
            print("Listening timed out. Try speaking again.")
        except Exception as e:
            print(f"An error occurred: {e}")
   