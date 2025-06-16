from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    path("ws/ai/", consumers.AIConsumer.as_asgi()),
    re_path(r'ws/camera/(?P<camera_id>\w+)/$', consumers.CameraStreamConsumer.as_asgi()),
]