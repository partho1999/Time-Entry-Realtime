import os
from ..add_cam.add_cam import get_all_cameras
from django.db import close_old_connections
from django.utils.timezone import now
from django.core.files.base import ContentFile
import cv2
import uuid
import time
import json
import base64
import numpy as np
import face_recognition
import threading
from datetime import datetime
from apps.models import Person, LoginHistory




# ───── Camera Setup ──────────────────────────────────────────
camera_urls = get_all_cameras()
camera_frames = {}
camera_locks = {}
last_detection_time = {}

# ───── Load Face Encodings ───────────────────────────────────
# getting person_id_no and image_text/base64 data 
def load_user_encodings():
    """
    Decodes base64 image_text for each person and extracts the 128-d face encoding.
    Returns:
        - List of 128-d numpy arrays
        - List of corresponding Person objects
    """
    close_old_connections()

    encodings = []
    users = []

    persons = Person.objects.select_related('image').all()
    for person in persons:
        img_base64 = getattr(person.image, 'image_text', None)
        if not img_base64:
            continue

        try:
            image_data = base64.b64decode(img_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            enc = face_recognition.face_encodings(rgb_img)

            if enc:
                encodings.append(enc[0])
                users.append(person)
        except Exception as e:
            print(f"[ENCODING ERROR] Person ID {person.id}: {e}")

    return encodings, users


#───── Camera Thread Function ────────────────────────────────
def capture_camera(cam_id, url):
    cap = None
    while True:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print(f"[ERROR] Failed to open {cam_id}")
                time.sleep(5)
                continue

        ret, frame = cap.read()
        if not ret:
            print(f"[WARNING] No frame from {cam_id}")
            time.sleep(2)
            continue

        with camera_locks[cam_id]:
            camera_frames[cam_id] = frame

        time.sleep(1)

# ───── Start All Camera Threads ──────────────────────────────
def start_all_camera_threads():
    for cam_id, url in camera_urls.items():
        camera_frames[cam_id] = None
        camera_locks[cam_id] = threading.Lock()
        last_detection_time[cam_id] = 0
        threading.Thread(target=capture_camera, args=(cam_id, url), daemon=True).start()
    print("[CAMERA] Threads started.")

# ───── Face Login Processor ──────────────────────────────────
def process_login(cam_id, frame):
    now = time.time()
    if now - last_detection_time[cam_id] < 2:
        return None

    if frame is None:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, face_locations)

    if not encodings or len(encodings) > 1:
        return None

    captured_encoding = encodings[0]

    known_encodings, known_users = load_user_encodings()
    if not known_encodings:
        return None

    distances = face_recognition.face_distance(known_encodings, captured_encoding)
    best_idx = np.argmin(distances)
    match_distance = float(distances[best_idx])
    user = known_users[best_idx] if match_distance < 0.5 else None

    _, buffer = cv2.imencode('.jpg', frame)
    live_b64 = base64.b64encode(buffer).decode('utf-8')
    status = "Granted" if user else "Denied"

    image_file = ContentFile(buffer.tobytes())
    filename = f"live_{uuid.uuid4().hex}.jpg"

    # Create LoginHistory instance
    login_record = LoginHistory(
        id_no=str(user.id) if user else "0",
        name=user.name if user else "Unknown",
        cam_id=str(cam_id),
        status=status
    )

    # Assign captured image
    login_record.live_capture.save(filename, image_file, save=False)

    # Assign registered image if available
    if user and hasattr(user, 'image') and user.image and user.image.image:
        login_record.registered_image = user.image.image

    login_record.save()


    # login_entry = LoginHistory(
    #     user_id=user.id if user else 0,
    #     name=user.name if user else "Unknown",
    #     camera_id=cam_id,
    #     registered_image="",  # can be added if needed
    #     live_capture=live_b64,
    #     status=status,
    #     login_time=datetime.utcnow()
    # )

  

