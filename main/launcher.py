import multiprocessing
from camera import vision_process
from assistant import assistant_process
from visualization import visualization_process


def main():
    # Create a shared queue for passing recognized names from vision -> assistant
    shared_queue = multiprocessing.Queue()
    message_queue = multiprocessing.Queue()
    signal_queue = multiprocessing.Queue()
    viz_queue = multiprocessing.Queue()

    manager = multiprocessing.Manager()
    speaking_flag = manager.Value('b', False)

    # Create two separate processes
    p_camera = multiprocessing.Process(target=vision_process, args=(shared_queue,))
    p_assistant = multiprocessing.Process(target=assistant_process,
                                          args=(shared_queue, message_queue, signal_queue, viz_queue, speaking_flag))
    p_visualization = multiprocessing.Process(target=visualization_process, args=(signal_queue, viz_queue, speaking_flag))

    # Start them
    p_camera.start()
    p_assistant.start()
    p_visualization.start()

    try:
        while True:
            pass
            '''
            chat_signal = signal_queue.get()
            if chat_signal == "received":
                text = input("Type Your Message: ").strip()
                if text:
                    message_queue.put(text)
            else:
                print(f"Main: Got some other signal: {chat_signal}")
            '''

    except Exception as e:
        print("An error occurred in the main loop: %s", e)
    finally:
        viz_queue.put("quit")


if __name__ == "__main__":
    main()
