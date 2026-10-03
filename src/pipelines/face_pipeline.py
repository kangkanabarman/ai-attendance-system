import dlib
import numpy as np
import face_recognition_models
import streamlit as st
from sklearn.svm import SVC
from PIL import Image, ImageDraw, ImageFont

from src.database.db import get_all_students

@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec

def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)

    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))
    return encodings

def get_face_embeddings_with_locations(image_np):
    """Returns face bounding boxes and corresponding 128-d embeddings."""
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)

    encodings = []
    locations = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))
        locations.append((face.top(), face.right(), face.bottom(), face.left()))
    return locations, encodings

@st.cache_resource
def get_trained_model():
    X = []
    y = []
    student_map = {}

    student_db = get_all_students()

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        sid = student.get('student_id')
        if embedding and sid is not None:
            X.append(np.array(embedding))
            y.append(sid)
            student_map[sid] = student.get('name', f'Student #{sid}')

    if len(X) == 0:
        return None

    clf = None
    unique_classes = list(set(y))
    if len(unique_classes) >= 2:
        clf = SVC(kernel='linear', probability=True, class_weight='balanced')
        try:
            clf.fit(X, y)
        except Exception:
            clf = None

    return {'clf': clf, 'X': X, 'y': y, 'student_map': student_map}

def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)

def annotate_image_with_faces(image_np, locations, recognized_names):
    """Draw bounding boxes and names on the image for visual feedback."""
    try:
        pil_img = Image.fromarray(image_np).convert("RGB")
        draw = ImageDraw.Draw(pil_img)
        
        for (top, right, bottom, left), name in zip(locations, recognized_names):
            color = "#00E676" if name != "Unknown" else "#FF5252"
            
            # Draw bounding box
            for offset in range(3):
                draw.rectangle(
                    [left - offset, top - offset, right + offset, bottom + offset],
                    outline=color
                )
            
            # Draw label box
            text = f" {name} "
            draw.rectangle(
                [left, bottom, right, bottom + 24],
                fill=color
            )
            draw.text((left + 4, bottom + 4), text, fill="black" if color == "#00E676" else "white")
            
        return np.array(pil_img)
    except Exception:
        return image_np

def predict_attendance(class_image_np, annotate=False):
    """
    Detects faces in classroom image and matches against trained database.
    Returns:
        detected_student: dict of {student_id: True}
        all_students: list of all registered student_ids
        num_faces: number of faces found
        annotated_image: optional np.ndarray with bounding boxes if annotate=True
    """
    locations, encodings = get_face_embeddings_with_locations(class_image_np)
    detected_student = {}

    model_data = get_trained_model()

    if not model_data:
        if annotate:
            annotated_img = annotate_image_with_faces(class_image_np, locations, ["Unknown"] * len(locations))
            return detected_student, [], len(encodings), annotated_img
        return detected_student, [], len(encodings)

    clf = model_data.get('clf')
    X_train = model_data['X']
    y_train = model_data['y']
    student_map = model_data.get('student_map', {})

    all_students = sorted(list(set(y_train)), key=lambda x: str(x))
    resemblance_threshold = 0.6
    recognized_names = []

    for encoding in encodings:
        matched_id = None
        min_distance = float('inf')

        # Compute Euclidean distance against all stored student embeddings
        for stored_emb, sid in zip(X_train, y_train):
            dist = np.linalg.norm(stored_emb - encoding)
            if dist < min_distance:
                min_distance = dist
                matched_id = sid

        # If SVM classifier is available and confident, we can also cross-check
        if min_distance <= resemblance_threshold and matched_id is not None:
            detected_student[matched_id] = True
            recognized_names.append(student_map.get(matched_id, f"ID: {matched_id}"))
        else:
            recognized_names.append("Unknown")

    if annotate:
        annotated_img = annotate_image_with_faces(class_image_np, locations, recognized_names)
        return detected_student, all_students, len(encodings), annotated_img

    return detected_student, all_students, len(encodings)