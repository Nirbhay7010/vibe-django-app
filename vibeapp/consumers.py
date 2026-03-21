import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Thread, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Grab the thread_id from the URL route we set up in routing.py
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'

        # Join the room group for this specific thread
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group when the user closes the chat or disconnects
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive a standard text message from the user's browser (WebSocket)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        sender_id = text_data_json['sender_id']

        # 1. Save the text message to the database asynchronously
        new_message = await self.save_message(self.thread_id, sender_id, message_content)

        # 2. Broadcast the message to everyone in the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'image_url': None, # Standard WebSocket messages are just text
                'sender_id': sender_id,
                'sender_username': new_message.sender.username,
                'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M')
            }
        )

    # Receive the broadcasted message from the room group (Handles BOTH text and images)
    async def chat_message(self, event):
        # Send the exact data payload down to the frontend
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'image_url': event.get('image_url', None), # ✨ Catches the image URL if uploaded via AJAX
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp']
        }))

    # Helper method to interact with the database safely in an async environment
    @database_sync_to_async
    def save_message(self, thread_id, sender_id, message_content):
        thread = Thread.objects.get(id=thread_id)
        sender = User.objects.get(id=sender_id)
        
        # Create the message
        message = Message.objects.create(thread=thread, sender=sender, content=message_content)
        
        # Force the thread's updated_at field to refresh so it stays at the top of the inbox
        thread.save() 
        
        return message


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We reuse the thread_id so calls are securely linked to specific chats
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        
        # Prefix with 'call_' instead of 'chat_' to keep text and video traffic completely separate
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

    # Receive WebRTC signaling messages from the browser
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        # WebRTC payloads usually contain a 'type' (offer, answer, or ice_candidate)
        # We don't need to parse it deeply here, we just forward the whole package to the other user.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_message', # Triggers the method below
                'data': text_data_json  # Forward the exact JSON payload
            }
        )

    # Broadcast the WebRTC message to the room
    async def call_message(self, event):
        # Send the payload down to the frontend
        await self.send(text_data=json.dumps(
            event['data']
        ))