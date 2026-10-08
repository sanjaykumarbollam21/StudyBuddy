import httpx
from typing import List
from app.embeddings.base import EmbeddingProvider
from app.core.config import settings

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI Embeddings provider (text-embedding-3-small).
    Dimension: 1536.
    """

    def __init__(self, api_key: str = "", model_name: str = "text-embedding-3-small"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name
        self.dimension = 1536

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model_name

    async def embed_text(self, text: str) -> List[float]:
        results = await self.embed_texts([text])
        return results[0]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured for OpenAIEmbeddingProvider")

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI embedding API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
