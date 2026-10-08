import httpx
from typing import List
from app.embeddings.base import EmbeddingProvider
from app.core.config import settings

class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini Embeddings provider (text-embedding-004).
    Dimension: 768.
    """

    def __init__(self, api_key: str = "", model_name: str = "models/text-embedding-004"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.dimension = 768

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model_name

    async def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured for GeminiEmbeddingProvider")

        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:embedContent?key={self.api_key}"
        payload = {
            "model": self.model_name,
            "content": {"parts": [{"text": text}]}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini embedding API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["embedding"]["values"]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Batch embedding calls
        results = []
        for text in texts:
            vec = await self.embed_text(text)
            results.append(vec)
        return results
