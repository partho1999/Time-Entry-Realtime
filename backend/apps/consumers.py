from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import random

class AIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.keep_sending = True
        asyncio.create_task(self.send_random_numbers())

    async def disconnect(self, close_code):
        self.keep_sending = False

    async def send_random_numbers(self):
        while self.keep_sending:
            number = random.uniform(0, 100)  # Random float between 0 and 100
            await self.send(text_data=str(round(number, 2)))
            await asyncio.sleep(1)