# import cv2
# import numpy as np
# import face_recognition
# import base64

# def extract_face_encoding(image_file) -> list:
#     """
#     Extracts the face encoding (128-d vector) from a file-like image object.

#     Args:
#         image_file: An open binary image file (e.g., Django UploadedFile)

#     Returns:
#         list: 128-dimensional face encoding

#     Raises:
#         ValueError: If image is invalid or no face is found.
#     """
#     image_file.seek(0)
#     image_data = image_file.read()

#     npimg = np.frombuffer(image_data, np.uint8)
#     img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

#     if img is None:
#         raise ValueError("Invalid image file.")

#     rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     encodings = face_recognition.face_encodings(rgb_img)

#     if not encodings:
#         raise ValueError("No face found in the image.")

#     return encodings[0].tolist()