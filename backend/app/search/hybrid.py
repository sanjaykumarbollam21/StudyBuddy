import time
import re
import logging
from typing import List, Optional, Dict, Any
from app.embeddings.base import EmbeddingProvider
from app.repositories.vector_repository import VectorRepository
from app.search.semantic import SemanticSearchEngine
from app.search.keyword import KeywordSearchEngine
from app.search.ranking import SearchResultRanker

logger = logging.getLogger("study_buddy.search")

class KnowledgeSearchService:
    """
    Central search service combining semantic dense vector search,
    lexical keyword matching, query intent normalization, and result diversification.
    """

    def __init__(
        self,
        vector_repo: VectorRepository,
        embedding_provider: EmbeddingProvider,
    ):
        self.vector_repo = vector_repo
        self.embedding_provider = embedding_provider
        self.semantic_engine = SemanticSearchEngine(vector_repo, embedding_provider)
        self.keyword_engine = KeywordSearchEngine()
        self.ranker = SearchResultRanker()

    def normalize_query(self, raw_query: str) -> str:
        """
        Lightweight deterministic query preprocessing.
        Strips conversational prefixes while preserving core technical intent.
        """
        q = raw_query.strip()
        # Remove conversational prompts like "explain ... to me", "what does my material say about"
        patterns = [
            r"^(please\s+)?explain\s+(to\s+me\s+)?(what\s+is\s+|about\s+)?",
            r"^(what\s+is|what\s+are|tell\s+me\s+about)\s+",
            r"^(teach\s+me\s+about|teach\s+me)\s+",
            r"(\s+from\s+my\s+(notes|materials|book|slides|syllabus))",
            r"(\s+in\s+my\s+(notes|materials|book|slides|syllabus))",
        ]
        for pat in patterns:
            q = re.sub(pat, " ", q, flags=re.IGNORECASE).strip()

        # Collapse whitespace
        q = re.sub(r"\s+", " ", q)
        return q if q else raw_query.strip()

    async def search_semantic(
        self,
        user_id: str,
        query: str,
        top_k: int = 8,
        document_ids: Optional[List[str]] = None,
        subject: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        start_time = time.time()
        processed_query = self.normalize_query(query)

        results = await self.semantic_engine.search(
            user_id=user_id,
            query=processed_query,
            top_k=top_k,
            document_ids=document_ids,
            subject=subject,
            collection=collection,
        )

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[SemanticSearch] user_id={user_id} query='{processed_query}' "
            f"top_k={top_k} results={len(results)} duration={duration_ms}ms"
        )
        return results

    async def search_hybrid(
        self,
        user_id: str,
        query: str,
        top_k: int = 8,
        document_ids: Optional[List[str]] = None,
        subject: Optional[str] = None,
        collection: Optional[str] = None,
        alpha: float = 0.7,
    ) -> List[Dict[str, Any]]:
        start_time = time.time()
        processed_query = self.normalize_query(query)

        # 1. Retrieve semantic candidates
        semantic_candidates = await self.semantic_engine.search(
            user_id=user_id,
            query=processed_query,
            top_k=top_k * 2,
            document_ids=document_ids,
            subject=subject,
            collection=collection,
        )

        # 2. Retrieve lexical candidates from user chunks
        all_user_chunks = await self.vector_repo.get_all_user_chunks_for_lexical(
            user_id=user_id,
            document_ids=document_ids,
            subject=subject,
            collection=collection,
        )

        keyword_candidates = self.keyword_engine.search(
            query=processed_query,
            candidates=all_user_chunks,
            top_k=top_k * 2,
        )

        # 3. Hybrid merge & diversification
        final_results = self.ranker.merge_hybrid(
            semantic_results=semantic_candidates,
            keyword_results=keyword_candidates,
            alpha=alpha,
            top_k=top_k,
        )

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[HybridSearch] user_id={user_id} query='{processed_query}' "
            f"sem_count={len(semantic_candidates)} kw_count={len(keyword_candidates)} "
            f"merged={len(final_results)} duration={duration_ms}ms"
        )
        return final_results
