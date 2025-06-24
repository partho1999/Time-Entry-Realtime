# apps/consumers.py

import cv2
import json
import asyncio
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.models import Camera, LoginHistory
from apps.services.face_login.face_login import process_face_login
from apps.services.camera_utils.camera_utils import build_rtsp_url
import logging

logger = logging.getLogger(__name__)

class CameraStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
            logger.info("WebSocket connection accepted")

            self.camera_id = self.scope['url_route']['kwargs']['camera_id']
            logger.info(f"Connecting to camera ID: {self.camera_id}")

            self.camera = await self.get_camera()
            if not self.camera:
                await self.send(json.dumps({'error': f'Camera {self.camera_id} not found'}))
                await self.close()
                return

            logger.info(f"Connected to camera: {self.camera.cam_name}")
            self.frame_queue = asyncio.Queue(maxsize=5)
            self.stream_task = asyncio.create_task(self.stream_camera())
            self.login_task = asyncio.create_task(self.process_login())

        except Exception as e:
            logger.exception("WebSocket connection error:")
            await self.send(json.dumps({'error': f'Connection error: {str(e)}'}))
            await self.close()

    @sync_to_async
    def get_camera(self):
        try:
            return Camera.objects.get(id=self.camera_id)
        except Camera.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: code={close_code}")
        if hasattr(self, 'stream_task') and not self.stream_task.cancelled():
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                logger.info("Stream task cancelled")
        if hasattr(self, 'login_task') and not self.login_task.cancelled():
            self.login_task.cancel()
            try:
                await self.login_task
            except asyncio.CancelledError:
                logger.info("Login task cancelled")

    async def stream_camera(self):
        rtsp_url = build_rtsp_url(self.camera)
        logger.info(f"[Camera {self.camera_id}] Connecting to RTSP: {rtsp_url}")

        loop = asyncio.get_event_loop()
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            logger.error(f"[Camera {self.camera_id}] Failed to open RTSP stream")
            await self.send(json.dumps({'error': 'Failed to open RTSP stream'}))
            await self.close()
            return

        logger.info(f"[Camera {self.camera_id}] RTSP stream opened")

        try:
            while True:
                ret, frame = await loop.run_in_executor(None, cap.read)
                if not ret:
                    logger.warning(f"[Camera {self.camera_id}] RTSP read failed")
                    break

                frame = await loop.run_in_executor(None, cv2.resize, frame, (320, 240))
                _, jpeg = await loop.run_in_executor(None, cv2.imencode, '.jpg', frame)
                await self.send(bytes_data=jpeg.tobytes())

                try:
                    self.frame_queue.put_nowait(frame)
                except asyncio.QueueFull:
                    pass

                await asyncio.sleep(0.01)
        except Exception as e:
            logger.exception("Error during streaming:")
            await self.send(json.dumps({'error': f'Streaming error: {str(e)}'}))
        finally:
            await self.frame_queue.put(None)  # Signal login task to stop
            cap.release()
            logger.info(f"[Camera {self.camera_id}] RTSP stream closed")

    async def process_login(self):
        try:
            while True:
                frame = await self.frame_queue.get()
                if frame is None:
                    break  # End of stream

                result = await process_face_login(frame, cam_id=self.camera.cam_id)
                await self.send(text_data=json.dumps(result))
                await asyncio.sleep(2)
        except Exception as e:
            logger.exception("Login processing error:")
            await self.send(json.dumps({'error': f'Login error: {str(e)}'}))

class LoginHistoryCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        while True:
            count = await self.get_login_history_count()
            await self.send(json.dumps({'count': count}))
            await asyncio.sleep(1)

    async def disconnect(self, close_code):
        pass

    @staticmethod
    @sync_to_async
    def get_login_history_count():
        return LoginHistory.objects.count()
