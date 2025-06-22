# apps/services/face_login/face_login.py

import cv2
import uuid
import numpy as np
import face_recognition
import faiss
import json
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from apps.models import PersonImage, LoginHistory

# Cache variables
_registered_encodings = None
_registered_metadata = None
_faiss_index = None

@sync_to_async
def load_registered_faces():
    global _registered_encodings, _registered_metadata, _faiss_index
    encodings = []
    metadata = []
    for record in PersonImage.objects.select_related('person').all():
        if record.face_encoding:
            try:
<<<<<<< HEAD
                # Safer parsing than eval: assume face_encoding is JSON string of list
                encoding_list = json.loads(record.face_encoding)
                encoding_array = np.array(encoding_list).astype('float32')
                encodings.append(encoding_array)
                metadata.append({
=======
                # Convert string representation back to list, then to numpy array
                encoding_list = eval(record.face_encoding)
                encoding_array = np.array(encoding_list)
                results.append({
>>>>>>> 554335878d3fd49dba55303e7d316642c605128d
                    "id_no": record.person.id_no,
                    "name": record.person.name,
                    "image": record.image
                })
<<<<<<< HEAD
            except Exception:
=======
            except Exception as e:
                print(f"Error processing face encoding: {e}")
>>>>>>> 554335878d3fd49dba55303e7d316642c605128d
                continue
    if encodings:
        _registered_encodings = np.vstack(encodings)
        _registered_metadata = metadata
        _faiss_index = faiss.IndexFlatL2(_registered_encodings.shape[1])  # L2 distance
        _faiss_index.add(_registered_encodings)
    else:
        _registered_encodings = np.empty((0, 128), dtype='float32')  # face_recognition encodings are 128 dim
        _registered_metadata = []
        _faiss_index = None

async def refresh_registered_faces():
    await load_registered_faces()

@sync_to_async
def log_login_attempt(name, id_no, cam_id, status, registered_img, live_img_bytes):
    live_img_name = f"live_{uuid.uuid4().hex}.jpg"
    live_file = ContentFile(live_img_bytes, name=live_img_name)
    LoginHistory.objects.create(
        name=name,
        id_no=id_no,
        cam_id=cam_id,
        status=status,
        registered_image=registered_img,
        live_capture=live_file
    )

async def process_face_login(frame, cam_id, threshold=0.45):
    global _faiss_index, _registered_metadata

    if _faiss_index is None or _registered_encodings is None:
        await refresh_registered_faces()

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return {"status": "No face detected"}

<<<<<<< HEAD
    for encoding in face_encodings:
        encoding_np = np.array(encoding).astype('float32').reshape(1, -1)
        distances, indices = _faiss_index.search(encoding_np, k=1)
        if indices.size > 0:
            idx = indices[0][0]
            dist = distances[0][0]
            if dist < threshold * threshold:  # FAISS returns squared L2 distance
                reg = _registered_metadata[idx]
=======
    registered_data = await get_all_registered_encodings()
    if not registered_data:
        print("No registered faces found in database")
        return {"status": "No registered faces found"}

    for encoding in face_encodings:
        for reg in registered_data:
            # Increase tolerance to 0.6 (default face_recognition value)
            match = face_recognition.compare_faces([reg["encoding"]], encoding, tolerance=0.6)
            if match[0]:
                print(f"Match found for {reg['name']}")
>>>>>>> 554335878d3fd49dba55303e7d316642c605128d
                _, jpeg_img = cv2.imencode(".jpg", frame)
                await log_login_attempt(
                    name=reg["name"],
                    id_no=reg["id_no"],
                    cam_id=cam_id,
                    status="Granted",
                    registered_img=reg["image"],
                    live_img_bytes=jpeg_img.tobytes()
                )
                return {"status": "Access Granted", "name": reg["name"], "id_no": reg["id_no"]}

    # No match found
    _, jpeg_img = cv2.imencode(".jpg", frame)
    await log_login_attempt(
        name="Unknown",
        id_no="Unknown",
        cam_id=cam_id,
        status="Denied",
        registered_img=None,
        live_img_bytes=jpeg_img.tobytes()
    )
    return {"status": "Access Denied"}

