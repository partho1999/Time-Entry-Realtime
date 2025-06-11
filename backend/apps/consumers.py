from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import json
from apps.services.face_login.face_login import process_login  # Should return a dict

class AIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.keep_sending = True
        self.task = asyncio.create_task(self.send_login_data())

    async def disconnect(self, close_code):
        self.keep_sending = False
        if hasattr(self, 'task'):
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def send_login_data(self):
        while self.keep_sending:
            try:
                # adapt this to whether process_login is async or sync
                login_entry = await asyncio.to_thread(process_login)
                await self.send(text_data=json.dumps(login_entry))
            except Exception as e:
                await self.send(text_data=json.dumps({"error": str(e)}))
            await asyncio.sleep(5)