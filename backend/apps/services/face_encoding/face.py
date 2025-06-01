import cv2
import numpy as np
import face_recognition
import base64
from io import BytesIO

def extract_face_encoding(image_data) -> list:
    """
    Extracts the face encoding (128-d vector) from image data.

    Args:
        image_data: Either a file-like object or bytes containing the image data

    Returns:
        list: 128-dimensional face encoding

    Raises:
        ValueError: If image is invalid or no face is found.
    """
    # Handle both file objects and bytes
    if hasattr(image_data, 'seek'):
        image_data.seek(0)
        image_bytes = image_data.read()
    else:
        image_bytes = image_data

    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Invalid image file.")

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_img)

    if not encodings:
        raise ValueError("No face found in the image.")

    return encodings[0].tolist()