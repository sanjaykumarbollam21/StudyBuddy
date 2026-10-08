from typing import List, Optional, Dict, Any
from app.embeddings.base import EmbeddingProvider
from app.repositories.vector_repository import VectorRepository

class SemanticSearchEngine:
    """
    Vector semantic similarity search engine.
    Encodes query text to dense vector and retrieves top-k matching chunks.
    """

    def __init__(self, vector_repo: VectorRepository, embedding_provider: EmbeddingProvider):
        self.vector_repo = vector_repo
        self.embedding_provider = embedding_provider

    async def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 8,
        document_ids: Optional[List[str]] = None,
        subject: Optional[str] = None,
        collection: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embedding_provider.embed_text(query)

        results = await self.vector_repo.search_similar_chunks(
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
            subject=subject,
            collection=collection,
            min_similarity=min_similarity,
        )

        for res in results:
            res["score_type"] = "semantic"

        return results
