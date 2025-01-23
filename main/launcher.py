# launcher.py
import multiprocessing
from camera import vision_process
from assistant import assistant_process

if __name__ == "__main__":
    # Create a shared queue for passing recognized names from vision -> assistant
    shared_queue = multiprocessing.Queue()

    # Create two separate processes
    p_camera = multiprocessing.Process(target=vision_process, args=(shared_queue,))
    p_assistant = multiprocessing.Process(target=assistant_process, args=(shared_queue,))

    # Start them
    p_camera.start()
    p_assistant.start()

    # Wait for them to finish
    p_camera.join()
    p_assistant.join()
