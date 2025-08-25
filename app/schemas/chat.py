from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    type: Literal["message", "system"]
    timestamp: datetime
    nickname: Optional[str] = None
    text: str

    def to_dict(self):
        return {
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "nickname": self.nickname,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=data["type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            nickname=data.get("nickname"),
            text=data["text"],
        )
