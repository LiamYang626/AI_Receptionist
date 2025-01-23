import pickle
import re
import face_recognition
import numpy as np


def encode_file(encoding_file, name_file):
    print("Reading Data from Files.")
    with open(encoding_file, 'rb') as fileEncodings, open(name_file, 'rb') as filePersons:
        print('Loading process data from files...')
        encoded_lists = pickle.load(fileEncodings)
        name_lists = pickle.load(filePersons)
        for i in range(len(name_lists)):
            names = name_lists[i].upper()
            names = re.search(r'[a-zA-Z ,-]+', names).group()  # only select the name
            names = names.replace("-", " ")
            names = names.strip()
            name_lists[i] = names
        print('Files Loaded.')
    return encoded_lists, name_lists


def recognizing_face(frame_people, encode_list, face_names, threshold=0.4, margin=0.01):
    frame_face = face_recognition.face_locations(frame_people, model="hog")
    encode_face_lists = face_recognition.face_encodings(frame_people, frame_face)

    if not encode_face_lists:  # Check if no face encodings were found
        print("No face encodings detected in the frame.")
        return ""

    encode_face = encode_face_lists[0]
    face_dis = face_recognition.face_distance(encode_list, encode_face)
    top_5_indices_not_sorted = np.argpartition(face_dis, 5)[:5]

    top_5_indices = top_5_indices_not_sorted[np.argsort(face_dis[top_5_indices_not_sorted])]

    min_dis_index = top_5_indices[0]

    second_dis_index = None
    for i in top_5_indices[1:]:  # Skip the first one, look for second distinct match
        if face_names[top_5_indices[0]] != face_names[i]:
            second_dis_index = i
            break

    if second_dis_index is None:
        name = face_names[min_dis_index]
    elif face_dis[second_dis_index] - face_dis[min_dis_index] >= margin and face_dis[min_dis_index] < threshold:
        name = face_names[min_dis_index]
    else:
        name = ""

    return name
