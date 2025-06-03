import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.models import Camera

def get_all_cameras():
    """
    Fetch and display all cameras from the database
    """
    try:
        cameras = Camera.objects.all()
        
        if not cameras:
            print("No cameras found in the database.")
            return
        
        # print("\n=== Camera List ===")
        # print("Total cameras found:", len(cameras))
        # print("\nDetailed Information:")
        # print("-" * 50)
        camera_dict = {}
        for cam in cameras:
            # print(f"\nCamera ID: {camera.cam_id}")
            # print(f"Name: {camera.cam_name}")
            # print(f"IP Address: {camera.cam_ip}")
            # print(f"Position: {camera.cam_position}")
            # print("-" * 50)
            key = f"{cam.cam_id}"
            value = f"rtsp://{cam.cam_name}:{cam.cam_password}@{cam.cam_ip}/channel=1/subtype=0"
            camera_dict[key] = value
        print("camera_dict:",camera_dict)
        return camera_dict

            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

# if __name__ == "__main__":
#     get_all_cameras()