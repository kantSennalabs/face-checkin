from PIL import Image, ImageDraw
import face_recognition
import cv2
import numpy as np
import pickle

# Name and image path
def register_face(name=None, image=None ,checkin = None):
    if len(face_recognition.face_locations(np.array(image))) != 1:
        return False
        
    known_faces = []
    known_face_names = []
    file = open("face/staff.txt", "r")
    lines = file.readlines()
    for line in lines:
        known_face_names.append(f"{line.strip()}")

    if name:
        if name not in [known_face_name.split(' ')[0] for known_face_name in known_face_names]:
            file = open("face/staff.txt", "a")
            file.write(f"{name} {checkin}")
            file.write("\n")
            known_face_names.append(f"{name} {checkin}")
            
        with open("face/staff.txt", "r") as f:
            lines = f.readlines()
        with open("face/staff.txt", "w") as f:
            for line in lines:
                if name in line:
                    f.write(f"{name} {checkin}")
                    f.write("\n")
                else:
                    f.write(line)
                    
        cv2.imwrite(f"face/{name}.jpg", image)

    for known_face_name in known_face_names:
        known_faces.append((f"{known_face_name.split(' ')[0]}", f"face/{known_face_name.split(' ')[0]}.jpg"))
        
    print("Registered name:", known_face_names)
    # Encode faces from images
    known_face_encodings = []
    for face in known_faces:
        # known_face_names.append(face[0])
        face_image = face_recognition.load_image_file(face[1])
        face_encoding = face_recognition.face_encodings(face_image)[0]
        known_face_encodings.append(face_encoding)

    # Dump face names and encoding to pickle
    pickle.dump((known_face_names, known_face_encodings), open("face/faces.p", "wb"))

    return True 