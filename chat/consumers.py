import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # only logged-in users may chat
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        # subscribe this connection to the room's group in Redis
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
        text_data_json = json.loads(text_data)   # JSON string -> Python dict
        message = text_data_json['message']      # the key set by the client's JS

        # Save the message to the database, with who sent it
        await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

    # the database is synchronous, so the save is wrapped for this async consumer
    @database_sync_to_async
    def save_message(self, message):
        Message.objects.create(room_name=self.room_name, sender=self.scope['user'], message_text=message)