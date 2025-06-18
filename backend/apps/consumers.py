# apps/consumers.py

import cv2
import json
import uuid
import asyncio
import numpy as np
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.files.base import ContentFile
from apps.models import Camera
from apps.services.face_login.face_login import process_face_login

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
                logger.error(f"Camera {self.camera_id} not found")
                await self.send(text_data=json.dumps({
                    'error': f'Camera {self.camera_id} not found'
                }))
                await self.close()
                return

            logger.info(f"Connected to camera: {self.camera.cam_name}")
            await self.stream_camera()

        except Exception as e:
            logger.exception("Error in WebSocket connection:")
            await self.send(text_data=json.dumps({
                'error': f'Connection error: {str(e)}'
            }))
            await self.close()

    @sync_to_async
    def get_camera(self):
        try:
            return Camera.objects.get(id=self.camera_id)
        except Camera.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: code={close_code}")

    async def stream_camera(self):
        rtsp_url = f"rtsp://{self.camera.cam_name}:{self.camera.cam_password}@{self.camera.cam_ip}/channel=1/subtype=0"
        logger.info(f"Connecting to RTSP stream: {rtsp_url}")

        loop = asyncio.get_event_loop()
        cap = await loop.run_in_executor(None, cv2.VideoCapture, rtsp_url)

        if not cap.isOpened():
            logger.error("Failed to open RTSP stream")
            await self.send(text_data=json.dumps({'error': 'Failed to open RTSP stream'}))
            await self.close()
            return

        logger.info("RTSP stream opened successfully")

        try:
            while True:
                ret, frame = await loop.run_in_executor(None, cap.read)
                if not ret:
                    logger.warning("Failed to read frame from RTSP")
                    break

                # Optional: Send live video preview to client (base64 or binary JPEG)
                _, jpeg_buffer = await loop.run_in_executor(None, cv2.imencode, '.jpg', frame)
                await self.send(bytes_data=jpeg_buffer.tobytes())

                # Process face login on current frame
                login_result = await process_face_login(frame, cam_id=self.camera.cam_id)
                await self.send(text_data=json.dumps(login_result))

                await asyncio.sleep(2)  # Optional throttle

        except Exception as e:
            logger.exception("Error during streaming:")
            await self.send(text_data=json.dumps({'error': f'Streaming error: {str(e)}'}))

        finally:
            await loop.run_in_executor(None, cap.release)
            logger.info("RTSP stream closed")
            await self.close()
