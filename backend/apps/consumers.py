from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import json
from apps.services.face_login.face_login import process_login  # Should return a dict
import cv2
import numpy as np
from asgiref.sync import sync_to_async
from .models import Camera
import logging

logger = logging.getLogger(__name__)

class AIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.keep_sending = True
        self.task = asyncio.create_task(self.send_login_data())

    async def disconnect(self, close_code):
        self.keep_sending = False
        if hasattr(self, 'task'):
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def send_login_data(self):
        while self.keep_sending:
            try:
                # adapt this to whether process_login is async or sync
                login_entry = await asyncio.to_thread(process_login)
                await self.send(text_data=json.dumps(login_entry))
            except Exception as e:
                await self.send(text_data=json.dumps({"error": str(e)}))
            await asyncio.sleep(5)

class CameraStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Allow all connections for now
            await self.accept()
            logger.info("WebSocket connection accepted")
            
            self.camera_id = self.scope['url_route']['kwargs']['camera_id']
            logger.info(f"Attempting to connect to camera: {self.camera_id}")
            
            self.camera = await self.get_camera()
            
            if not self.camera:
                logger.error(f"Camera not found: {self.camera_id}")
                await self.send(text_data=json.dumps({
                    'error': f'Camera {self.camera_id} not found'
                }))
                await self.close()
                return
                
            logger.info(f"Found camera: {self.camera.cam_name}")
            await self.stream_camera()
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
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
        except Exception as e:
            logger.error(f"Error getting camera: {str(e)}")
            return None

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code: {close_code}")

    async def stream_camera(self):
        rtsp_url = f"rtsp://{self.camera.cam_name}:{self.camera.cam_password}@{self.camera.cam_ip}/channel=1/subtype=0"
        logger.info(f"Attempting to connect to RTSP URL: {rtsp_url}")
        
        try:
            # Run OpenCV operations in a thread pool
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(None, cv2.VideoCapture, rtsp_url)
            
            if not cap.isOpened():
                logger.error("Failed to open RTSP stream")
                await self.send(text_data=json.dumps({
                    'error': 'Failed to open RTSP stream'
                }))
                await self.close()
                return
            
            logger.info("RTSP stream opened successfully")
            
            while True:
                try:
                    # Read frame in thread pool
                    ret, frame = await loop.run_in_executor(None, cap.read)
                    if not ret:
                        logger.error("Failed to read frame from RTSP stream")
                        break
                        
                    # Encode frame to JPEG in thread pool
                    _, buffer = await loop.run_in_executor(None, cv2.imencode, '.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    
                    # Send frame as binary data
                    await self.send(bytes_data=frame_bytes)
                    
                except Exception as e:
                    logger.error(f"Error processing frame: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in stream_camera: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': f'Streaming error: {str(e)}'
            }))
        finally:
            if 'cap' in locals():
                await loop.run_in_executor(None, cap.release)
                logger.info("RTSP stream released")
            await self.close()