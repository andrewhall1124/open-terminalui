import json
import sqlite3
from datetime import datetime
from pathlib import Path

from ._models import Chat, Message


class ChatManager:
    """Manages chat persistence using SQLite database"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the chat manager with SQLite database.

        Args:
            db_path: Path to the SQLite database file. If None, defaults to
                    ~/.open-terminalui/chats.db
        """
        if db_path is None:
            # Default to ~/.open-terminalui/chats.db
            app_dir = Path.home() / ".open-terminalui"
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / "chats.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Initialize the database schema.

        Creates the chats table if it doesn't exist with columns for id, title,
        messages_json, created_at, and updated_at.
        """
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
        """
        Create a new chat and save it to the database.

        Args:
            title: The title for the chat. If None, generates a default title
                  with the current date and time (e.g., "Chat 2025-12-11 14:30")

        Returns:
            A new Chat object with an assigned ID and empty message list
        """
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
        """
        Save or update a chat in the database.

        If the chat has no ID (newly created), inserts it as a new record.
        If the chat has an ID (existing), updates the existing record.
        Automatically updates the updated_at timestamp.

        Args:
            chat: The Chat object to save. The chat.id will be set if it's a new chat.
        """
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
        """
        Load a chat from the database by its ID.

        Args:
            chat_id: The unique identifier of the chat to load

        Returns:
            The Chat object if found, None if no chat exists with the given ID
        """
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

    def list_chats(self) -> list[Chat]:
        """
        List all chats from the database.

        Returns:
            List of all Chat objects ordered by updated_at timestamp in descending order
            (most recently updated first). Returns empty list if no chats exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, messages_json, title, created_at, updated_at FROM chats ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
        # messages_json = json.dumps([msg.to_dict() for msg in chat.messages])

        chats = []
        for row in rows:
            messages_data = json.loads(row["messages_json"])
            messages = [
                Message(role=msg["role"], content=msg["content"])
                for msg in messages_data
            ]
            chats.append(
                Chat(
                    row["id"],
                    row["title"],
                    messages,
                    datetime.fromisoformat(row["updated_at"]),
                    datetime.fromisoformat(row["updated_at"]),
                )
            )

        return chats

    def delete_chat(self, chat_id: int):
        """
        Delete a chat from the database.

        Args:
            chat_id: The unique identifier of the chat to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
