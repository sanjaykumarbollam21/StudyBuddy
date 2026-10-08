from typing import Optional
from app.core.config import settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.local import LocalEmbeddingProvider
from app.embeddings.gemini import GeminiEmbeddingProvider
from app.embeddings.openai import OpenAIEmbeddingProvider

_provider_cache = {}

def get_embedding_provider(name: Optional[str] = None) -> EmbeddingProvider:
    """
    Factory to instantiate or return cached embedding provider based on configuration.
    Defaults to settings.EMBEDDING_PROVIDER ('local', 'gemini', or 'openai').
    """
    provider_name = (name or settings.EMBEDDING_PROVIDER or "local").lower().strip()

    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    if provider_name == "gemini":
        provider = GeminiEmbeddingProvider()
    elif provider_name == "openai":
        provider = OpenAIEmbeddingProvider()
    else:
        provider = LocalEmbeddingProvider(
            dimension=settings.EMBEDDING_DIMENSION,
            model_name=settings.EMBEDDING_MODEL,
        )

    _provider_cache[provider_name] = provider
    return provider
