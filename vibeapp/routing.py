from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This regex route captures the thread_id for TEXT CHAT
    # Example: ws://yourdomain/ws/chat/5/ connects to Thread ID 5
    re_path(r'ws/chat/(?P<thread_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    
    # This regex route captures the thread_id for VIDEO CALL SIGNALING
    # Example: ws://yourdomain/ws/call/5/ connects to Thread ID 5
    re_path(r'ws/call/(?P<thread_id>\d+)/$', consumers.CallConsumer.as_asgi()),
]