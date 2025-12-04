import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import Chat, Message


class ChatStorage:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            # Default to ~/.open-terminalui/chats.db
            app_dir = Path.home() / ".open-terminalui"
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / "chats.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    messages_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_chat(self, title: str | None = None) -> Chat:
        """Create a new chat"""
        if title is None:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        now = datetime.now()
        messages_json = json.dumps([])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO chats (title, messages_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, messages_json, now.isoformat(), now.isoformat()),
            )
            conn.commit()
            chat_id = cursor.lastrowid

        return Chat(
            id=chat_id, title=title, messages=[], created_at=now, updated_at=now
        )

    def save_chat(self, chat: Chat):
        """Save or update a chat"""
        messages_json = json.dumps([msg.to_dict() for msg in chat.messages])
        chat.updated_at = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            if chat.id is None:
                # Chat doesn't exist in DB yet, insert it
                cursor = conn.execute(
                    "INSERT INTO chats (title, messages_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (
                        chat.title,
                        messages_json,
                        chat.created_at.isoformat(),
                        chat.updated_at.isoformat(),
                    ),
                )
                chat.id = cursor.lastrowid
            else:
                # Chat exists, update it
                conn.execute(
                    "UPDATE chats SET title = ?, messages_json = ?, updated_at = ? WHERE id = ?",
                    (chat.title, messages_json, chat.updated_at.isoformat(), chat.id),
                )
            conn.commit()

    def load_chat(self, chat_id: int) -> Chat | None:
        """Load a chat by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
            row = cursor.fetchone()

        if row is None:
            return None

        messages_data = json.loads(row["messages_json"])
        messages = [
            Message(role=msg["role"], content=msg["content"]) for msg in messages_data
        ]

        return Chat(
            id=row["id"],
            title=row["title"],
            messages=messages,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def list_chats(self) -> list[tuple[int, str, datetime]]:
        """List all chats (id, title, updated_at)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, title, updated_at FROM chats ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()

        return [
            (row["id"], row["title"], datetime.fromisoformat(row["updated_at"]))
            for row in rows
        ]

    def delete_chat(self, chat_id: int):
        """Delete a chat by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
