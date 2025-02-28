# visualization.py
import wave
import numpy as np
import pyaudio
import matplotlib.pyplot as plt
import time


def visualization_process(signal_queue, queue, speaking_flag):
    """
    A long-running process that keeps a persistent visualization window open.
    It checks the queue for new visualization commands (tuples of (wav_path, sentence)).
    When a new command is received, it plays the audio and updates the waveform continuously.
    """
    plt.ion()  # Turn on interactive mode
    fig, (ax_wave, ax_log) = plt.subplots(2, 1, figsize=(10, 8),
                                            gridspec_kw={'height_ratios': [3, 1]})
    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()

    # Setup the waveform axis
    ax_wave.get_xaxis().set_visible(False)
    ax_wave.get_yaxis().set_visible(False)
    ax_wave.set_frame_on(False)
    chunk = 1024
    x = np.arange(0, chunk)
    line, = ax_wave.plot(x, np.zeros(chunk), '-', lw=2)
    ax_wave.set_ylim(-30000, 30000)
    ax_wave.set_xlim(0, chunk)

    # Text overlay for sentence
    text_annotation = ax_wave.text(0.5, 0.05, "",
                                   transform=ax_wave.transAxes,
                                   ha='center', va='bottom',
                                   fontsize=24, color='black')
    # Setup log axis (optional)
    ax_log.axis('off')
    log_text = ax_log.text(0, 1, "",
                           transform=ax_log.transAxes,
                           ha='left', va='top',
                           fontsize=14, color='black')

    current_command = None

    while True:
        # Check for new command (non-blocking)
        try:
            if not signal_queue.empty():
                signal = str(signal_queue.get())
                text_annotation.set_text(signal)

            if not queue.empty():
                command = queue.get_nowait()
                if command == "quit":
                    break
                else:
                    current_command = command

        except Exception:
            pass

        if current_command:
            wav_path, sentence = current_command
            try:
                wf = wave.open(wav_path, 'rb')
            except Exception as e:
                print(f"Error opening {wav_path}: {e}")
                current_command = None
                continue

            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            duration = wf.getnframes() / sample_rate

            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=n_channels,
                            rate=sample_rate,
                            output=True)

            words = sentence.split()
            total_frames = wf.getnframes()
            current_frame = 0

            # Play audio and update visualization continuously
            while current_frame < total_frames:
                data = wf.readframes(chunk)
                if not data:
                    break
                stream.write(data)
                current_frame += chunk

                # Update waveform plot
                audio_data = np.frombuffer(data, dtype=np.int16)
                if n_channels > 1:
                    audio_data = audio_data[::n_channels]
                if len(audio_data) < chunk:
                    audio_data = np.pad(audio_data, (0, chunk - len(audio_data)), mode='constant')
                line.set_ydata(audio_data)

                # Update text overlay based on playback progress
                current_time = current_frame / sample_rate
                progress = current_time / duration if duration > 0 else 1
                current_word_index = int(progress * len(words))
                if current_word_index >= len(words):
                    current_word_index = len(words) - 1
                words_str = r'\;'.join([
                    r'\mathbf{' + word + '}' if idx == current_word_index else r'\mathrm{' + word + '}'
                    for idx, word in enumerate(words)
                ])
                text_annotation.set_text("$" + words_str + "$")

                # Optionally, update log_text here if you have logs to display

                fig.canvas.draw()
                fig.canvas.flush_events()
                # Short pause to allow GUI update
                plt.pause(0.01)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
            # After finishing one command, reset to wait for the next one
            speaking_flag.value = False
            current_command = None

        # Keep the loop alive so the window stays open
        plt.pause(0.1)
        time.sleep(0.01)
