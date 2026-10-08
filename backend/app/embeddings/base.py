from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding generation providers.
    Supports local, Gemini, and OpenAI embedding models.
    """

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate a dense vector embedding for a single text."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a batch of texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the vector dimension produced by this provider."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier name."""
        pass
