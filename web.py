import eel 
from chat.connect import *


def web_process():
    
    eel.init("Interface")

    play_sound()

    @eel.expose
    def init():
        # subprocess.call(['./device.sh'])
        eel.hideStart()
        play_sound()

    os.system('open -a "Google Chrome" "http://localhost:8000/index.html"')

    eel.start('index.html', mode=None, host='localhost', block=True)
