import multiprocessing
from camera import vision_process
from assistant import assistant_process
from server import run_server
import os
import time


def main():
    # Create a shared queue for passing recognized names from vision -> assistant
    shared_queue = multiprocessing.Queue()

    # Create two separate processes
    p_camera = multiprocessing.Process(target=vision_process, args=(shared_queue,))
    p_server = multiprocessing.Process(target=run_server)
    p_assistant = multiprocessing.Process(target=assistant_process,
                                          args=(shared_queue, ))
    
    # Start them
    p_camera.start()
    p_server.start()
    p_assistant.start()
    time.sleep(2)
    os.system('open -a "Google Chrome" "http://127.0.0.1:5500/Interface/index.html"')

    p_camera.join()
    p_assistant.join()
    p_server.join()


if __name__ == "__main__":
    main()
