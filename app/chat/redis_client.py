import json
import logging

import redis.asyncio as redis

from app.core.config import settings
from app.schemas.chat import ChatMessage

logger = logging.getLogger("note_app.chat")


class RedisClient:
    def __init__(self):
        self.redis = None
        self.connected = False

    async def connect(self):
        try:
            connection_params = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "password": settings.REDIS_PASSWORD,
                "encoding": "utf-8",
                "decode_responses": True,
                "ssl": False,
            }

            if hasattr(settings, "REDIS_USERNAME") and settings.REDIS_USERNAME:
                connection_params["username"] = settings.REDIS_USERNAME

            self.redis = redis.Redis(**connection_params)
            await self.redis.ping()
            self.connected = True
            logger.info("Successfully connected to Redis Cloud")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        if self.redis and self.connected:
            try:
                await self.redis.close()
                self.connected = False
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")

    async def is_connected(self) -> bool:
        if not self.redis or not self.connected:
            return False
        try:
            await self.redis.ping()
            return True
        except:
            self.connected = False
            return False

    async def add_chat_message(self, message: ChatMessage):
        if not await self.is_connected():
            logger.warning("Redis not connected - cannot save message")
            return False

        try:
            message_data = json.dumps(message.to_dict())
            await self.redis.lpush("chat:history", message_data)
            await self.redis.ltrim("chat:history", 0, 99)
            logger.debug(f"Message saved to Redis: {message.text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error adding message to Redis: {e}")
            return False

    async def get_recent_messages(self, limit: int = 20) -> list[ChatMessage]:
        if not await self.is_connected():
            logger.warning("Redis not connected - returning empty message list")
            return []

        try:
            messages_json = await self.redis.lrange("chat:history", 0, limit - 1)
            messages = []
            for msg_json in reversed(messages_json):
                try:
                    msg_data = json.loads(msg_json)
                    messages.append(ChatMessage.from_dict(msg_data))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error parsing Redis message: {e}")

            logger.debug(f"Retrieved {len(messages)} messages from Redis")
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from Redis: {e}")
            return []


redis_client = RedisClient()
