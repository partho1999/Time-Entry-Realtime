import cv2
import time
import uuid
import base64
import threading
import numpy as np
from datetime import datetime

from django.db import close_old_connections, connection
from django.core.files.base import ContentFile

import face_recognition

from apps.models import Person, LoginHistory
from apps.services.add_cam.add_cam import get_all_cameras

# ───── Camera Setup ──────────────────────────────────────────
camera_urls = get_all_cameras()
camera_frames = {}
camera_locks = {}
last_detection_time = {}
camera_threads_started = set()

MATCH_THRESHOLD = 0.6  # Lower is stricter, tune as needed

# ───── Global storage for user encodings ─────────────────────
# Load once, refresh periodically to avoid DB hits every login attempt
user_encodings = []
user_objects = []
encodings_lock = threading.Lock()

def load_user_encodings():
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

def refresh_encodings_periodically(interval=300):
    """Background thread to refresh user encodings every `interval` seconds."""
    global user_encodings, user_objects
    while True:
        try:
            new_encodings, new_users = load_user_encodings()
            with encodings_lock:
                user_encodings = new_encodings
                user_objects = new_users
            print(f"[ENCODINGS] Refreshed {len(new_encodings)} user encodings.")
        except Exception as e:
            print(f"[ENCODINGS] Failed to refresh: {e}")
        time.sleep(interval)

# ───── Camera Thread Function ────────────────────────────────
def capture_camera(cam_id, url):
    close_old_connections()
    cap = None
    while True:
        try:
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(url)
                if not cap.isOpened():
                    print(f"[ERROR] Failed to open camera {cam_id}")
                    time.sleep(5)
                    continue

            ret, frame = cap.read()
            if not ret:
                print(f"[WARNING] No frame from camera {cam_id}")
                time.sleep(2)
                continue

            with camera_locks[cam_id]:
                camera_frames[cam_id] = frame
        except Exception as e:
            print(f"[ERROR] Exception in camera {cam_id} capture: {e}")
            if cap:
                cap.release()
                cap = None
            time.sleep(5)

        time.sleep(1)  # Adjust as needed for frame rate

    close_old_connections()

# ───── Start All Camera Threads ──────────────────────────────
def start_all_camera_threads():
    for cam_id, url in camera_urls.items():
        if cam_id not in camera_threads_started:
            camera_frames[cam_id] = None
            camera_locks[cam_id] = threading.Lock()
            last_detection_time[cam_id] = 0
            t = threading.Thread(target=capture_camera, args=(cam_id, url), daemon=True)
            t.start()
            camera_threads_started.add(cam_id)
    print("[CAMERA] Threads started.")

# Start encoding refresh thread once on module load
threading.Thread(target=refresh_encodings_periodically, daemon=True).start()

# ───── Face Login Processor ──────────────────────────────────
def process_login(cam_id):
    now_time = time.time()
    if now_time - last_detection_time.get(cam_id, 0) < 2:  # Debounce 2 seconds per camera
        return None

    frame = None
    with camera_locks[cam_id]:
        frame = camera_frames.get(cam_id)

    if frame is None:
        return None

    try:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, face_locations)

        if not encodings or len(encodings) != 1:
            return None

        captured_encoding = encodings[0]

        with encodings_lock:
            if not user_encodings:
                return None

            distances = face_recognition.face_distance(user_encodings, captured_encoding)
            best_idx = np.argmin(distances)
            match_distance = float(distances[best_idx])
            user = user_objects[best_idx] if match_distance < MATCH_THRESHOLD else None

        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            return None

        live_b64 = base64.b64encode(buffer).decode('utf-8')
        status = "Granted" if user else "Denied"

        image_file = ContentFile(buffer.tobytes())
        filename = f"live_{uuid.uuid4().hex}.jpg"

        # Save login record
        login_entry = LoginHistory(
            id_no=str(user.id) if user else "0",
            name=user.name if user else "Unknown",
            cam_id=str(cam_id),
            status=status,
        )

        login_entry.live_capture.save(filename, image_file, save=False)

        if user and hasattr(user, 'image') and user.image and user.image.image:
            login_entry.registered_image = user.image.image

        login_entry.save()

        last_detection_time[cam_id] = now_time
        return login_entry

    except Exception as e:
        print(f"[PROCESS LOGIN ERROR] Camera {cam_id}: {e}")
        return None
