import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import apps.routing  # adjust to your app name

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timeEntry.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(apps.routing.websocket_urlpatterns)
    ),
})
