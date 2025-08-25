import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import WebSocket

from app.schemas.chat import ChatMessage

from .redis_client import redis_client

logger = logging.getLogger("note_app.chat")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_nicknames: Dict[str, str] = {}
        self.memory_history: List[ChatMessage] = []

    async def add_message_to_history(self, message: ChatMessage):
        try:
            if await redis_client.is_connected():
                data = json.dumps(message.to_dict(), ensure_ascii=False)
                await redis_client.redis.lpush("chat:history", data)
                await redis_client.redis.ltrim("chat:history", 0, 99)
                return
        except Exception as e:
            logger.error(f"Redis save error: {e}")
        self.memory_history.append(message)
        if len(self.memory_history) > 100:
            self.memory_history = self.memory_history[-100:]

    async def get_recent_history(self, limit: int = 20) -> List[ChatMessage]:
        try:
            if await redis_client.is_connected():
                raw = await redis_client.redis.lrange("chat:history", 0, limit - 1)
                out: List[ChatMessage] = []
                for item in reversed(raw):
                    try:
                        out.append(ChatMessage.from_dict(json.loads(item)))
                    except Exception as e:
                        logger.error(f"Parse error: {e}")
                return out
        except Exception as e:
            logger.error(f"Redis read error: {e}")
        return self.memory_history[-limit:] if self.memory_history else []

    async def connect(self, websocket: WebSocket, nickname: str):
        ws_id = str(id(websocket))
        self.active_connections[ws_id] = websocket
        self.user_nicknames[ws_id] = nickname

        logger.info(
            f"User '{nickname}' connected. Active users: {len(self.active_connections)}"
        )

        for msg in await self.get_recent_history(20):
            try:
                await websocket.send_json(msg.to_dict())
            except Exception as e:
                logger.error(f"Error sending history: {e}")

        join = ChatMessage(
            type="system",
            timestamp=datetime.now(timezone.utc),
            text=f"{nickname} присоединился к чату",
        )
        await self.broadcast_message(join)
        await self.add_message_to_history(join)

    async def disconnect(self, websocket: WebSocket):
        ws_id = str(id(websocket))
        nickname = self.user_nicknames.pop(ws_id, None)
        self.active_connections.pop(ws_id, None)

        if not nickname:
            logger.info(f"Disconnect unknown socket {ws_id}; silent drop")
            return

        leave = ChatMessage(
            type="system",
            timestamp=datetime.now(timezone.utc),
            text=f"{nickname} покинул чат",
        )
        try:
            await self.broadcast_message(leave)
            await self.add_message_to_history(leave)
        except Exception as e:
            logger.warning(f"Broadcast on disconnect failed: {e}")

        logger.info(
            f"User '{nickname}' disconnected. Active users: {len(self.active_connections)}"
        )

    async def broadcast_message(
        self, message: ChatMessage, exclude: Optional[WebSocket] = None
    ):
        payload = message.to_dict()
        dead: List[str] = []
        for ws_id, conn in list(self.active_connections.items()):
            if exclude is not None and conn is exclude:
                continue
            try:
                await conn.send_json(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to {ws_id}: {e}")
                dead.append(ws_id)
        for ws_id in dead:
            self.active_connections.pop(ws_id, None)
            self.user_nicknames.pop(ws_id, None)

    async def handle_user_message(self, websocket: WebSocket, text: str):
        ws_id = str(id(websocket))
        nickname = self.user_nicknames.get(ws_id, "Гость")
        msg = ChatMessage(
            type="message",
            timestamp=datetime.now(timezone.utc),
            nickname=nickname,
            text=text,
        )
        await self.broadcast_message(msg)
        await self.add_message_to_history(msg)
        logger.info(f"[{nickname}] {text[:50]}...")


manager = ConnectionManager()
