import json
from datetime import datetime

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, dict[int, WebSocket]] = {}

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(room_id, {})[user_id] = websocket

    def disconnect(self, room_id: int, user_id: int):
        if room_id in self.active:
            self.active[room_id].pop(user_id, None)
            if not self.active[room_id]:
                del self.active[room_id]

    async def broadcast(self, room_id: int, message: dict, skip_user: int | None = None):
        for uid, ws in list(self.active.get(room_id, {}).items()):
            if skip_user and uid == skip_user:
                continue
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.disconnect(room_id, uid)

    def online_users(self, room_id: int) -> list[int]:
        return list(self.active.get(room_id, {}).keys())


chat_manager = ConnectionManager()
