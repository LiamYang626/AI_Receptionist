# launcher.py
import multiprocessing
from camera import vision_process
from assistant import assistant_process


def main():
    # Create a shared queue for passing recognized names from vision -> assistant
    shared_queue = multiprocessing.Queue()
    message_queue = multiprocessing.Queue()
    ask_queue = multiprocessing.Queue()

    # Create two separate processes
    p_camera = multiprocessing.Process(target=vision_process, args=(shared_queue,))
    p_assistant = multiprocessing.Process(target=assistant_process, args=(shared_queue, message_queue, ask_queue))

    # Start them
    p_camera.start()
    p_assistant.start()

    while True:
        ask_signal = ask_queue.get()
        if ask_signal == "received":
            text = input("Type Your Message: ")
            if not text.strip():
                continue

            # Place the typed message onto the user_input_queue
            message_queue.put(text)
        else:
            print(f"Main: Got some other signal: {ask_signal}")

    # Wait for them to finish
    # p_camera.join()
    # p_assistant.join()


if __name__ == "__main__":
    main()
