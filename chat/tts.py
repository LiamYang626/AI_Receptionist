from pydub import AudioSegment
import os
import subprocess
import requests
import time


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


def openai_transcribe_audio(client, filepath: str) -> str:
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
