import hashlib
from pathlib import Path
from typing import List, Tuple

import chromadb
import ollama

from open_terminalui._models import Chat, Message


class MemoryManager:
    """Manages chat message vector embeddings using ChromaDB"""

    def __init__(self, storage_path: str | None = None):
        """Initialize the document manager with ChromaDB client"""
        if storage_path is None:
            # Default to ~/.open-terminalui/chroma_db
            app_dir = Path.home() / ".open-terminalui"
            app_dir.mkdir(exist_ok=True)
            storage_path = str(app_dir / "chroma_db")

        self.storage_path = storage_path
        self.client = chromadb.PersistentClient(path=storage_path)

        # Get or create the documents collection
        self.collection = self.client.get_or_create_collection(
            name="chat-message-summaries",
            metadata={"description": "Chat message summaries with embeddings"},
        )

    def _get_chat_message_hash(self, chat_id: int, message_index: int) -> str:
        """Generate a hash for the file to use as unique identifier"""
        return hashlib.md5(f"{chat_id}-{message_index}".encode()).hexdigest()

    def _summarize_message(self, message: Message, min_length: int = 200) -> str | None:
        """
        Summarize a message if it exceeds min_length, otherwise return original content.

        Args:
            message: The message to summarize
            min_length: Minimum character length to trigger summarization (default: 200)

        Returns:
            Summary if message is long enough, otherwise original content
        """
        # If message is short, return it as-is without summarization
        if len(message.content) < min_length:
            return message.content

        prompt = f"""Help me build your memory by summarizing this message from the user into just the facts:

Message: {message.content}

Provide only the summary without labels:
"""

        ollama_request = [{"role": "user", "content": prompt}]

        try:
            ollama_response = ollama.chat(
                model="llama3.2", messages=ollama_request, stream=False
            )

            message_summary = ollama_response.message.content

            if message_summary is not None:
                return message_summary

        except Exception as e:
            raise Exception(e)

    def save_chat(self, chat: Chat):
        """
        Save chat messages to the vector store with embeddings.

        Processes each user and assistant message in the chat, summarizes them if needed,
        and stores them in ChromaDB for semantic search. Skips messages that have already
        been saved.

        Args:
            chat: The chat object containing messages to save
        """
        if chat.id is None:
            return

        chat_id = chat.id
        for message_index, message in enumerate(chat.messages):
            # Only index user and assistant messages (skip log messages)
            if message.role not in ("user", "assistant"):
                continue

            chat_message_hash = self._get_chat_message_hash(chat_id, message_index)
            existing = self.collection.get(
                where={"chat_message_hash": chat_message_hash}
            )

            # Check if message has already been saved
            if existing and existing["ids"]:
                return None

            message_summary = self._summarize_message(message)

            if message_summary is None:
                continue

            metadata = {
                "chat_id": chat_id,
                "message_index": message_index,
                "chat_message_hash": chat_message_hash,
            }

            self.collection.add(
                ids=[chat_message_hash],
                documents=[message_summary],
                metadatas=[metadata],
            )

    def delete_chat(self, chat_id: int):
        """Delete all message summaries associated with a chat"""
        # Query for all documents with this chat_id
        try:
            results = self.collection.get(where={"chat_id": chat_id})

            # Delete all matching documents
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])

        except Exception as e:
            raise Exception(f"Failed to delete chat {chat_id}: {e}")

    def list_chat_summaries(self) -> List[Tuple[int, int, str]]:
        """
        List all chat summaries in the vector store

        Returns:
            List of tuples: (chat_id, message_count, chat_message_hashes)
        """
        try:
            # Get all chat summaries
            results = self.collection.get()

            if not results["metadatas"]:
                return []

            # Group by chat_id to get unique chats
            chats_by_id = {}
            for metadata in results["metadatas"]:
                chat_id = metadata["chat_id"]
                if chat_id not in chats_by_id:
                    chats_by_id[chat_id] = {"message_count": 0, "hashes": []}
                chats_by_id[chat_id]["message_count"] += 1
                chats_by_id[chat_id]["hashes"].append(metadata["chat_message_hash"])

            # Convert to list of tuples
            return [
                (chat_id, chat_data["message_count"], ", ".join(chat_data["hashes"]))
                for chat_id, chat_data in chats_by_id.items()
            ]

        except Exception as _:
            return []

    def search_chat_summaries(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Search chat message summaries using semantic similarity.

        Performs a vector similarity search across all stored chat message summaries
        and returns the most relevant results.

        Args:
            query: The search query text
            top_k: Maximum number of results to return (default: 5)

        Returns:
            List of tuples containing (document_text, similarity_score) where
            similarity_score is between 0 and 1, with 1 being most similar

        Raises:
            Exception: If the search operation fails
        """
        try:
            results = self.collection.query(query_texts=[query], n_results=top_k)

            if not results["documents"] or not results["documents"][0]:
                return []

            chunks = []
            documents = results["documents"][0]
            distances = results["distances"][0] if results["distances"] else []

            for i, doc in enumerate(documents):
                # ChromaDB returns distances, lower is better
                # Convert to similarity score (1 - normalized_distance)
                distance = distances[i] if distances else 0
                similarity = max(0, 1 - distance)

                chunks.append((doc, similarity))

            return chunks

        except Exception as e:
            raise Exception(e)
