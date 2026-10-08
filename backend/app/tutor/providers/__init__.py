from typing import Optional
import os
from app.core.config import settings
from app.tutor.providers.base import LLMProvider
from app.tutor.providers.gemini import GeminiLLMProvider
from app.tutor.providers.openai import OpenAILLMProvider
from app.tutor.providers.mock import MockLLMProvider

_llm_cache = {}

def get_llm_provider(name: Optional[str] = None) -> LLMProvider:
    """
    Factory to return configured Cloud LLM provider.
    In testing environments (PYTEST_CURRENT_TEST or ENVIRONMENT=='test'),
    returns MockLLMProvider for deterministic offline validation unless a specific provider is requested.
    In production, resolves configured cloud provider (Gemini or OpenAI).
    """
    is_testing = "PYTEST_CURRENT_TEST" in os.environ or settings.ENVIRONMENT == "test"

    # In test runs without explicit provider request, always return deterministic MockLLMProvider
    if is_testing and name is None:
        return MockLLMProvider()

    default_name = settings.AI_DEFAULT_PROVIDER or "gemini"
    provider_name = (name or default_name).lower().strip()

    if not is_testing and provider_name in _llm_cache:
        return _llm_cache[provider_name]

    if provider_name in ["llama_cpp", "llamacpp", "llama-cpp"]:
        from app.tutor.providers.llama_cpp import LlamaCppLLMProvider
        provider = LlamaCppLLMProvider()
    elif provider_name.startswith("ollama"):
        from app.tutor.providers.ollama import OllamaLLMProvider
        provider = OllamaLLMProvider()
    elif provider_name == "mock":
        provider = MockLLMProvider()
    elif provider_name == "openai" and settings.OPENAI_API_KEY:
        provider = OpenAILLMProvider()
    elif provider_name == "gemini" and settings.GEMINI_API_KEY:
        provider = GeminiLLMProvider()
    else:
        # Default fallback
        if is_testing:
            provider = MockLLMProvider()
        elif settings.GEMINI_API_KEY:
            provider = GeminiLLMProvider()
        elif settings.OPENAI_API_KEY:
            provider = OpenAILLMProvider()
        else:
            provider = MockLLMProvider()

    if not is_testing:
        _llm_cache[provider_name] = provider
    return provider
