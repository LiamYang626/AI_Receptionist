from pydub import AudioSegment


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
