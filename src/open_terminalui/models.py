from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Chat:
    id: int | None
    title: str
    messages: list[Message]
    created_at: datetime
    updated_at: datetime

    def to_ollama_messages(self) -> list[dict]:
        """Convert messages to Ollama API format"""
        return [msg.to_dict() for msg in self.messages]

    @staticmethod
    def create_unsaved(title: str | None = None) -> "Chat":
        """Create a new chat that hasn't been saved to the database yet"""
        if title is None:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        now = datetime.now()
        return Chat(id=None, title=title, messages=[], created_at=now, updated_at=now)
