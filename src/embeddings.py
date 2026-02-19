"""
Embedding Model Module
======================

Provides sentence transformer embedding functionality for semantic task search.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Wrapper for sentence transformer embedding model."""

    def __init__(self, model_name: str):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model name (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text to embedding vector(s).

        Args:
            text: Single text string or list of texts

        Returns:
            Numpy array of embeddings (1D for single text, 2D for list)
        """
        embeddings = self.model.encode(text, convert_to_numpy=True)

        # Ensure float32 for sqlite-vec compatibility
        return embeddings.astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode single text to embedding vector.

        Args:
            text: Single text string

        Returns:
            Numpy array of embedding (1D float32)
        """
        return self.encode(text)

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        embeddings = self.encode([text1, text2])

        vec1 = embeddings[0]
        vec2 = embeddings[1]

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))


def get_embedding_model(model_name: str) -> EmbeddingModel:
    """
    Factory function to get embedding model instance.

    Args:
        model_name: HuggingFace model name

    Returns:
        Initialized EmbeddingModel instance
    """
    return EmbeddingModel(model_name)