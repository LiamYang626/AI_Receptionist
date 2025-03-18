import os
from playsound import playsound
  

def play_sound():
    sound_path = os.path.join('Interface', 'assets', 'audio', 'start_sound.mp3')
    playsound(sound_path)
