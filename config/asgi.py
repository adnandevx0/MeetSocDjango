import os

# Set Django settings FIRST before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from websocket.middleware import JWTAuthMiddlewareStack
from websocket.routing import websocket_urlpatterns

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
