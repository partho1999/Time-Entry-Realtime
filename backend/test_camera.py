# import os
# import django
# import cv2
# import time

# # Set up Django environment
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeEntry.settings')
# django.setup()

# from apps.models import Camera

# def test_camera_connection():
#     # Get camera from database
#     camera = Camera.objects.get(cam_id='CC1')
    
#     # Construct RTSP URL
#     rtsp_url = f"rtsp://{camera.cam_name}:{camera.cam_password}@{camera.cam_ip}:554/live"
#     print(f"Testing connection to: {rtsp_url}")
    
#     # Try to open the camera stream
#     cap = cv2.VideoCapture(rtsp_url)
    
#     if not cap.isOpened():
#         print("Failed to open camera stream")
#         return False
    
#     print("Successfully opened camera stream")
    
#     # Try to read a frame
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to read frame from camera")
#         cap.release()
#         return False
    
#     print("Successfully read frame from camera")
#     print(f"Frame shape: {frame.shape}")
    
#     # Release the camera
#     cap.release()
#     return True

# if __name__ == "__main__":
#     test_camera_connection() 