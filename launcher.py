import multiprocessing
import eel
from camera import vision_process
from assistant import assistant_process
from web import web_process


def main():

    # Create a shared queue for passing recognized names from vision -> assistant
    shared_queue = multiprocessing.Queue()
    message_queue = multiprocessing.Queue()
    signal_queue = multiprocessing.Queue()

    # Create a shared mode flag: 1 means text-only, 0 means voice mode.
    mode_flag = multiprocessing.Value('i', 1)  # start with text mode

    @eel.expose
    def send_message(text):
        message_queue.put(text)


    @eel.expose
    def toggle_mode(mode):
        # mode should be "text" or "voice"
        if mode == "text":
            mode_flag.value = 1
        elif mode == "voice":
            mode_flag.value = 0
        print("Mode switched to:", "Text-only" if mode_flag.value == 1 else "Voice")


    # Create two separate processes
    p_camera = multiprocessing.Process(target=vision_process, args=(shared_queue,))
    p_assistant = multiprocessing.Process(target=assistant_process,
                                          args=(shared_queue, message_queue, signal_queue, mode_flag))
    p_web = multiprocessing.Process(target=web_process)

     # Start them
    p_web.start()
    p_camera.start()
    p_assistant.start()
    p_web.join()


if __name__ == "__main__":
    main()
