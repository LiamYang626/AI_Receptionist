import eel
from playsound import playsound


@eel.expose
def playAssistantSound():
    music_dir = "interface\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)
