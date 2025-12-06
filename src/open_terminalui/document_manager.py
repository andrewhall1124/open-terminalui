import hashlib
import os
from pathlib import Path
from typing import List, Tuple

import chromadb
from chromadb.config import Settings
from pypdf import PdfReader


class DocumentManager:
    """Manages PDF documents and their vector embeddings using ChromaDB"""

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
            name="documents",
            metadata={"description": "PDF document chunks with embeddings"},
        )

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from a PDF file"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _chunk_text(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def _get_file_hash(self, file_path: str) -> str:
        """Generate a hash for the file to use as unique identifier"""
        return hashlib.md5(file_path.encode()).hexdigest()

    def add_document(self, file_path: str) -> Tuple[bool, str]:
        """
        Add a PDF document to the vector store

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate file exists and is a PDF
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        if not file_path.lower().endswith(".pdf"):
            return False, "Only PDF files are supported"

        try:
            # Check if document already exists
            file_hash = self._get_file_hash(file_path)
            existing = self.collection.get(where={"file_hash": file_hash})

            if existing and existing["ids"]:
                return False, f"Document already exists: {os.path.basename(file_path)}"

            # Extract text from PDF
            text = self._extract_text_from_pdf(file_path)

            if not text.strip():
                return False, "PDF appears to be empty or contains no extractable text"

            # Chunk the text
            chunks = self._chunk_text(text)

            # Generate IDs and metadata for each chunk
            file_name = os.path.basename(file_path)
            ids = [f"{file_hash}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "file_path": file_path,
                    "file_name": file_name,
                    "file_hash": file_hash,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                for i in range(len(chunks))
            ]

            # Add to ChromaDB (it will automatically generate embeddings)
            self.collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas,
            )

            return True, f"Successfully added {len(chunks)} chunks from {file_name}"

        except Exception as e:
            return False, f"Error adding document: {str(e)}"

    def remove_document(self, file_path: str) -> Tuple[bool, str]:
        """
        Remove a document from the vector store

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            file_hash = self._get_file_hash(file_path)

            # Get all chunks for this document
            results = self.collection.get(where={"file_hash": file_hash})

            if not results["ids"]:
                return False, f"Document not found: {os.path.basename(file_path)}"

            # Delete all chunks
            self.collection.delete(ids=results["ids"])

            return True, f"Successfully removed {os.path.basename(file_path)}"

        except Exception as e:
            return False, f"Error removing document: {str(e)}"

    def list_documents(self) -> List[Tuple[str, str, int]]:
        """
        List all documents in the vector store

        Returns:
            List of tuples: (file_path, file_name, num_chunks)
        """
        try:
            # Get all documents
            results = self.collection.get()

            if not results["metadatas"]:
                return []

            # Group by file_hash to get unique documents
            docs_by_hash = {}
            for metadata in results["metadatas"]:
                file_hash = metadata["file_hash"]
                if file_hash not in docs_by_hash:
                    docs_by_hash[file_hash] = {
                        "file_path": metadata["file_path"],
                        "file_name": metadata["file_name"],
                        "chunk_count": 0,
                    }
                docs_by_hash[file_hash]["chunk_count"] += 1

            # Convert to list of tuples
            return [
                (doc["file_path"], doc["file_name"], doc["chunk_count"])
                for doc in docs_by_hash.values()
            ]

        except Exception as e:
            return []

    def search_documents(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Search for relevant document chunks using vector similarity

        Args:
            query: The search query
            top_k: Number of top results to return

        Returns:
            List of tuples: (chunk_text, file_name, similarity_score)
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            chunks = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                # ChromaDB returns distances, lower is better
                # Convert to similarity score (1 - normalized_distance)
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = max(0, 1 - distance)

                chunks.append((doc, metadata["file_name"], similarity))

            return chunks

        except Exception as e:
            return []
