import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.models import Camera

# apps/services/camera_utils/camera_utils.py

def build_rtsp_url(camera):
    """
    Build RTSP URL for a single Camera instance.
    """
    try:
        rtsp_url = f"rtsp://{camera.cam_name}:{camera.cam_password}@{camera.cam_ip}/channel=1/subtype=0"
        return rtsp_url
    except Exception as e:
        print(f"Error building RTSP URL: {str(e)}")
        return None
