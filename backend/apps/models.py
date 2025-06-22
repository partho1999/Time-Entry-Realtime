from django.db import models
from django.utils import timezone
import base64
from io import BytesIO
from .services.face_encoding.face import extract_face_encoding

class Person(models.Model):
    name = models.CharField(max_length=100)
    # age = models.PositiveIntegerField()
    mobile_no = models.CharField(max_length=50)
    gender = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    id_no = models.CharField(max_length=100)
    email = models.EmailField()
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PersonImage(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='image')
    image = models.ImageField(upload_to='person_image/')
    image_text = models.TextField(blank=True, null=True)  # new field to store base64 string
    face_encoding = models.TextField(blank=True, null=True) 
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.image and not self.image_text:
            self.image.open()
            image_data = self.image.read()
            self.image_text = base64.b64encode(image_data).decode('utf-8')
            # Store face encoding as a string representation of a list
            encoding = extract_face_encoding(image_data)
            if encoding is not None:
                self.face_encoding = str(encoding)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image of {self.person.name}"

class PersonVisiting(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='visiting_info')
    card_no = models.CharField(max_length=100)
    visit_reason = models.CharField(max_length=100)
    visit_start_time = models.DateTimeField(null=True, blank=True)
    visit_end_time = models.DateTimeField(null=True, blank=True)
    visitor_group = models.CharField(max_length=10)
    respondent = models.CharField(max_length=100)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Visiting Info of {self.person.name}"

class Camera(models.Model):
    cam_id = models.CharField(max_length=100, unique=True)
    cam_name = models.CharField(max_length=255)
    cam_password = models.CharField(max_length=255)
    cam_ip = models.GenericIPAddressField()
    # cam_port = models.PositiveIntegerField()
    cam_position = models.CharField(max_length=255)

    def __str__(self):
        return self.cam_name

class LoginHistory(models.Model):
    id_no = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    cam_id = models.CharField(max_length=100)
    registered_image = models.ImageField(upload_to='registered_images/')
    live_capture = models.ImageField(upload_to='live_captures/')
    status = models.CharField(max_length=20, choices=[('Granted', 'Granted'), ('Denied', 'Denied')])
    login_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"


