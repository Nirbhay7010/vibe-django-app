"""
ASGI config for vibeproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibeproject.settings')

# Initialize standard Django HTTP handling first to prevent AppRegistry errors
django_asgi_app = get_asgi_application()

# Import Channels routing after initializing Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import vibeapp.routing 

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # Channels router to handle WebSocket connections
    "websocket": AuthMiddlewareStack(
        URLRouter(
            vibeapp.routing.websocket_urlpatterns
        )
    ),
})