import eel
import os
from playsound import playsound

eel.init('Interface')


def display(text):
    eel.DisplayText(text)
    eel.receiverText(text)


def speak(text):
    eel.DisplayMessage(text)
    eel.receiverText(text)
    

@eel.expose
def play_sound():
    sound_path = os.path.join('Interface', 'assets', 'audio', 'start_sound.mp3')
    playsound(sound_path)
