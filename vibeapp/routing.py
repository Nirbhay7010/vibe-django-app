from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<thread_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/call/(?P<thread_id>\d+)/$', consumers.CallConsumer.as_asgi()),
    
    # NEW: Route for live notifications
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]