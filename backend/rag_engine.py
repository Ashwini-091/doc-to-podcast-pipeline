import os
import pickle
from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from backend.utils import extract_text_from_file, chunk_text, log_metrics, MetricsTracker

class RAGEngine:
    """Retrieval-Augmented Generation engine using FAISS."""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", vector_db_path: str = "data/vectors"):
        """
        Initialize RAG engine.

        Args:
            embedding_model: HuggingFace model name for embeddings
            vector_db_path: Path to store FAISS index and metadata
        """
        self.vector_db_path = vector_db_path
        os.makedirs(vector_db_path, exist_ok=True)

        # Load embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # FAISS index
        self.index = None
        self.chunks = []
        self.metadata = {}

        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing FAISS index or create new one."""
        index_path = os.path.join(self.vector_db_path, "faiss_index.bin")
        chunks_path = os.path.join(self.vector_db_path, "chunks.pkl")
        metadata_path = os.path.join(self.vector_db_path, "metadata.pkl")

        if os.path.exists(index_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(chunks_path, 'rb') as f:
                    self.chunks = pickle.load(f)
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"Loaded FAISS index with {len(self.chunks)} chunks")
            except Exception as e:
                print(f"Error loading index: {e}. Creating new index.")
                self.index = faiss.IndexFlatL2(self.embedding_dim)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

    def add_document(self, file_path: str, doc_id: str = None):
        """
        Add a document to the RAG engine.

        Args:
            file_path: Path to document file
            doc_id: Unique document identifier
        """
        metrics_tracker = MetricsTracker()
        metrics_tracker.start_stage("document_processing")

        # Extract text
        text = extract_text_from_file(file_path)

        # Chunk text
        chunks = chunk_text(text, chunk_size=512, overlap=50)

        # Generate embeddings
        metrics_tracker.start_stage("embedding_generation")
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=True)
        embeddings = embeddings.astype(np.float32)
        metrics_tracker.end_stage("embedding_generation")

        # Add to FAISS index
        metrics_tracker.start_stage("index_update")
        start_idx = len(self.chunks)
        self.index.add(embeddings)

        # Store chunks and metadata
        for i, chunk in enumerate(chunks):
            chunk_idx = start_idx + i
            self.chunks.append(chunk)
            self.metadata[chunk_idx] = {
                "doc_id": doc_id or "unknown",
                "chunk_id": i,
                "content": chunk[:100]  # Store first 100 chars as preview
            }

        metrics_tracker.end_stage("index_update")
        metrics_tracker.end_stage("document_processing")

        # Save index
        self._save_index()

        print(f"Added {len(chunks)} chunks from {file_path}")
        return {
            "chunks_added": len(chunks),
            "total_chunks": len(self.chunks)
        }

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve top-k relevant chunks for a query.

        Args:
            query: Query text
            top_k: Number of top results to return

        Returns:
            List of (chunk_text, similarity_score) tuples
        """
        if len(self.chunks) == 0:
            return []

        # Encode query
        query_embedding = self.embedding_model.encode([query]).astype(np.float32)

        # Search in FAISS
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.chunks)))

        # Return chunks with similarity scores
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            idx_int = int(idx)
            if 0 <= idx_int < len(self.chunks):
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + distance)
                results.append((self.chunks[idx_int], similarity))

        return results

    def get_context(self, query: str, top_k: int = 5, max_tokens: int = 2000) -> str:
        """
        Get formatted context for a query, respecting token limit.

        Args:
            query: Query text
            top_k: Number of chunks to consider
            max_tokens: Maximum tokens in context

        Returns:
            Formatted context string
        """
        results = self.retrieve(query, top_k)

        context = "Based on the provided documents, here is relevant information:\n\n"
        token_count = 0

        for chunk, score in results:
            # Approximate token count (1 token ≈ 4 characters)
            chunk_tokens = len(chunk) // 4

            if token_count + chunk_tokens > max_tokens:
                break

            context += f"- {chunk}\n\n"
            token_count += chunk_tokens

        return context if token_count > 0 else "No relevant context found in the documents."

    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        faiss.write_index(self.index, os.path.join(self.vector_db_path, "faiss_index.bin"))

        with open(os.path.join(self.vector_db_path, "chunks.pkl"), 'wb') as f:
            pickle.dump(self.chunks, f)

        with open(os.path.join(self.vector_db_path, "metadata.pkl"), 'wb') as f:
            pickle.dump(self.metadata, f)

    def clear(self):
        """Clear the index."""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.chunks = []
        self.metadata = {}
        self._save_index()
        print("FAISS index cleared")
