import cv2
import time
import socket
import os
import csv
import random
import traceback
from vision.gaze import gaze
from vision.detector import detect_people
from vision.tracking import initialize_deepsort, track_objects
from vision.recognition import encode_file, recognizing_face
from vision.utils import initialize_object_detector, initialize_face_detector, initialize_landmark_detector
# from vision.visualization import draw_bounding_box

fileEncodingsName = 'models/encodings-everyone-2023-11-30-17-50-53-weekofcode2324.dat'
filePersonsNames = 'models/persons-everyone-2023-11-30-17-50-53-weekofcode2324.dat'
encodeListKnown, classNames = encode_file(fileEncodingsName, filePersonsNames)

# Set up the Face Mesh with refine_landmarks=True to get iris landmarks
face_mesh = initialize_landmark_detector()

# Set up Face Detector
face_detector = initialize_face_detector()

# Load YOLO model (using lightweight model yolov8n)
model = initialize_object_detector()

# Command-line arguments for camera source
cap = cv2.VideoCapture(0)

# Initialize DeepSORT tracker
deepsort = initialize_deepsort()

# To store the name associated with each tracked object (track_id)
track_id_to_name = {}


# Initialize socket for data transmission (optional)
SERVER_IP = "127.0.0.1"  # Set the server IP address (localhost)
SERVER_PORT = 7070  # Set the server port
SERVER_ADDRESS = (SERVER_IP, SERVER_PORT)
iris_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Prepare for CSV logging (optional)
LOG_DATA = True
LOG_FOLDER = "logs"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)
csv_data = []
column_names = [
    "Timestamp (ms)",
    "Gaze Data"
]


def vision_process(shared_queue):
    # Main loop
    current_selected_name = None
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Flip the frame horizontally for a selfie view and convert color from BGR to RGB
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            detection = detect_people(model, frame)

            # Pass detection results to DeepSORT and track
            tracked_objects = track_objects(deepsort, detection, frame=frame)

            # Get image dimensions
            height_frame, width_frame = frame.shape[:2]

            recognized_names = set()
            recognized_names.clear()

            for track in tracked_objects:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue

                track_id = track.track_id
                bbox = track.to_tlbr()
                x1, y1, x2, y2 = [int(i) for i in bbox]

                # Clip coordinates
                x1 = max(0, min(x1, width_frame - 1))
                y1 = max(0, min(y1, height_frame - 1))
                x2 = max(0, min(x2, width_frame - 1))
                y2 = max(0, min(y2, height_frame - 1))

                if track_id not in track_id_to_name:
                    person_frame = frame[y1:y2, x1:x2]
                    person_frame_rgb = cv2.cvtColor(person_frame, cv2.COLOR_BGR2RGB)
                    name = recognizing_face(person_frame_rgb, encodeListKnown, classNames)

                    if name != "":
                        track_id_to_name[track_id] = name

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                name = track_id_to_name.get(track_id, "")

                # Display the name if recognized
                if name != "":
                    text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    cv2.putText(frame, name, (x1 + (x2 - x1) // 2 - text_size[0] // 2, y1 - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                    # print(f"[Vision] Detected: {name}")
                    recognized_names.add(name)

            if recognized_names:
                # If the current selected name is not present, choose a new one.
                if current_selected_name not in recognized_names:
                    # You can choose the first one, or use random.choice(list(recognized_names))
                    current_selected_name = random.choice(list(recognized_names))
                    shared_queue.put(current_selected_name)

            else:
                # Clear selection when no names are recognized
                current_selected_name = None

            # Process the frame with Face Mesh
            results_mesh = face_mesh.process(rgb_frame)
            landmarks = getattr(results_mesh, 'multi_face_landmarks', None)

            if landmarks:
                # Perform gaze estimation
                gaze(frame, landmarks[0])

            # Display the result
            cv2.imshow('Camera', frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Exiting program...")
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
        pass

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        iris_socket.close()
        print("Program exited successfully.")

        # Writing data to CSV file (optional)
        if LOG_DATA:
            print("Writing data to CSV...")
            timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S")
            csv_file_name = os.path.join(LOG_FOLDER, f"gaze_log_{timestamp_str}.csv")
            with open(csv_file_name, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(column_names)  # Writing column names
                writer.writerows(csv_data)  # Writing data rows
            print(f"Data written to {csv_file_name}")
