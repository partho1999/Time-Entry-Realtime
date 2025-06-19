# apps/services/face_login.py

import cv2
import uuid
import numpy as np
import face_recognition
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from apps.models import PersonImage, LoginHistory, Camera
import asyncio



@sync_to_async
def get_all_registered_encodings():
    results = []
    for record in PersonImage.objects.select_related('person').all():
        if record.face_encoding:
            try:
                encoding_array = np.array(eval(record.face_encoding))  # stored as text
                results.append({
                    "id_no": record.person.id_no,
                    "name": record.person.name,
                    "encoding": encoding_array,
                    "image": record.image
                })
            except Exception as e:
                continue
    return results

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

async def process_face_login(frame, cam_id):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return {"status": "No face detected"}

    registered_data = await get_all_registered_encodings()
    for encoding in face_encodings:
        for reg in registered_data:
            match = face_recognition.compare_faces([reg["encoding"]], encoding, tolerance=0.45)
            if match[0]:
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

async def process_camera_stream(camera):
    rtsp_url = f"rtsp://{camera.cam_name}:{camera.cam_password}@{camera.cam_ip}/channel=1/subtype=0"
    print(f"[Camera {camera.cam_id}] Connecting to RTSP stream: {rtsp_url}")
    loop = asyncio.get_event_loop()
    cap = await loop.run_in_executor(None, cv2.VideoCapture, rtsp_url)
    if not cap.isOpened():
        print(f"[Camera {camera.cam_id}] Failed to open RTSP stream")
        return
    frame_queue = asyncio.Queue(maxsize=5)

    async def stream_frames():
        while True:
            ret, frame = await loop.run_in_executor(None, cap.read)
            if not ret:
                print(f"[Camera {camera.cam_id}] Failed to read frame from RTSP")
                break
            # Resize frame to low resolution for real-time streaming
            frame = await loop.run_in_executor(None, cv2.resize, frame, (320, 240))
            print(f"[Camera {camera.cam_id}] Streaming frame...")
            try:
                frame_queue.put_nowait(frame)
            except asyncio.QueueFull:
                pass
            await asyncio.sleep(0.01)

    async def process_login():
        while True:
            frame = await frame_queue.get()
            login_result = await process_face_login(frame, cam_id=camera.cam_id)
            print(f"[Camera {camera.cam_id}] Login result: {login_result}")
            await asyncio.sleep(2)

    try:
        await asyncio.gather(stream_frames(), process_login())
    finally:
        await loop.run_in_executor(None, cap.release)
        print(f"[Camera {camera.cam_id}] RTSP stream closed")

async def start_all_camera_threads():
    cameras = await sync_to_async(list)(Camera.objects.all())
    tasks = []
    for camera in cameras:
        task = asyncio.create_task(process_camera_stream(camera))
        tasks.append(task)
    await asyncio.gather(*tasks)
