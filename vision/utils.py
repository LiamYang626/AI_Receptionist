import mediapipe as mp
from ultralytics import YOLO


def initialize_object_detector():
    return YOLO("yolov8n.pt")


def initialize_face_detector():
    mp_face_detection = mp.solutions.face_detection

    detection = mp_face_detection.FaceDetection(
        min_detection_confidence=0.8,
    )

    return detection


def initialize_landmark_detector():
    mp_face_mesh = mp.solutions.face_mesh

    mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=5,
        refine_landmarks=True,  # Enable landmarks
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8
    )

    return mesh
