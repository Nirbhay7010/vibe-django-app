import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Thread, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        sender_id = text_data_json['sender_id']

        new_message = await self.save_message(self.thread_id, sender_id, message_content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'image_url': None, 
                'sender_id': sender_id,
                'sender_username': new_message.sender.username,
                'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'image_url': event.get('image_url', None), 
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, thread_id, sender_id, message_content):
        thread = Thread.objects.get(id=thread_id)
        sender = User.objects.get(id=sender_id)
        message = Message.objects.create(thread=thread, sender=sender, content=message_content)
        thread.save() 
        return message


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'call_{self.thread_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_message', 
                'data': text_data_json 
            }
        )

    async def call_message(self, event):
        await self.send(text_data=json.dumps(
            event['data']
        ))

# --- NEW: LIVE NOTIFICATION CONSUMER ---
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            # Create a unique group for this specific user
            self.group_name = f"notifs_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Catches the message from views.py and sends it to the frontend
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))