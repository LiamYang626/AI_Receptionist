import signal
import sys
import multiprocessing
from camera import vision_process
from assistant import assistant_process


def main():
    # Create a shared queue for passing recognized names from vision -> assistant
    shared_queue = multiprocessing.Queue()
    message_queue = multiprocessing.Queue()
    signal_queue = multiprocessing.Queue()

    # Create two separate processes
    p_camera = multiprocessing.Process(target=vision_process, args=(shared_queue,))
    p_assistant = multiprocessing.Process(target=assistant_process, args=(shared_queue, message_queue, signal_queue))

    # Start them
    p_camera.start()
    p_assistant.start()

    '''
    # Setup graceful shutdown handler
    def signal_handler(sig, frame):
        print("Shutdown signal received, terminating processes...")
        p_camera.terminate()
        p_assistant.terminate()
        p_camera.join()
        p_assistant.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    '''

    try:
        while True:
            chat_signal = signal_queue.get()
            if chat_signal == "received":
                text = input("Type Your Message: ").strip()
                if text:
                    message_queue.put(text)
            else:
                print(f"Main: Got some other signal: {chat_signal}")

    except Exception as e:
        print("An error occurred in the main loop: %s", e)
        # signal_handler(None, None)


if __name__ == "__main__":
    main()
