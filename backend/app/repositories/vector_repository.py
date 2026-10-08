import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk

class VectorRepository:
    """
    Repository for storing and querying chunk vector embeddings.
    Enforces strict user isolation on all retrieval operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0
        for a, b in zip(vec_a, vec_b):
            dot += a * b
            norm_a += a * a
            norm_b += b * b

        if norm_a <= 0.0 or norm_b <= 0.0:
            return 0.0

        sim = dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
        return max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))

    async def save_chunk_embedding(
        self,
        chunk_id: str,
        embedding: List[float],
        model_name: str,
    ) -> None:
        """Persist vector embedding for an individual chunk."""
        result = await self.session.execute(
            select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
        chunk = result.scalar_one_or_none()
        if chunk:
            chunk.embedding = embedding
            chunk.embedding_model = model_name
            chunk.embedded_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def save_batch_chunk_embeddings(
        self,
        chunk_embeddings: List[Tuple[str, List[float]]],
        model_name: str,
    ) -> None:
        """Persist vector embeddings for a batch of chunks."""
        if not chunk_embeddings:
            return

        chunk_ids = [cid for cid, _ in chunk_embeddings]
        emb_map = {cid: emb for cid, emb in chunk_embeddings}

        result = await self.session.execute(
            select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
        )
        chunks = result.scalars().all()
        now = datetime.now(timezone.utc)

        for chunk in chunks:
            if chunk.id in emb_map:
                chunk.embedding = emb_map[chunk.id]
                chunk.embedding_model = model_name
                chunk.embedded_at = now

        await self.session.commit()

    async def search_similar_chunks(
        self,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 8,
        document_ids: Optional[List[str]] = None,
        subject: Optional[str] = None,
        collection: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search chunks by vector cosine similarity.
        STRICT TENANT ISOLATION: Explicitly filters on chunk.user_id == user_id.
        User A can NEVER retrieve User B's chunks.
        """
        conditions = [
            DocumentChunk.user_id == user_id,
            DocumentChunk.embedding.isnot(None),
            Document.status != "failed",
        ]

        if document_ids:
            conditions.append(DocumentChunk.document_id.in_(document_ids))
        if subject:
            conditions.append(Document.subject_name == subject)
        if collection:
            conditions.append(Document.collection_name == collection)

        query = (
            select(DocumentChunk, Document.filename, Document.subject_name, Document.collection_name)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(and_(*conditions))
        )

        result = await self.session.execute(query)
        rows = result.all()
        if not rows:
            return []

        valid_rows = [r for r in rows if r[0].embedding and len(r[0].embedding) == len(query_embedding)]
        if not valid_rows:
            return []

        try:
            import numpy as np
            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = float(np.linalg.norm(q_vec))
            if q_norm > 0:
                q_vec /= q_norm

            matrix = np.array([r[0].embedding for r in valid_rows], dtype=np.float32)
            row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            row_norms[row_norms == 0] = 1e-9
            matrix /= row_norms

            # High-speed vectorized cosine dot product
            sims = np.dot(matrix, q_vec)
            sims = np.where(sims < 0, (sims + 1.0) / 2.0, sims)
            sims = np.clip(sims, 0.0, 1.0)

            scored_chunks = []
            for idx, sim in enumerate(sims):
                if float(sim) >= min_similarity:
                    chunk, filename, subject_name, collection_name = valid_rows[idx]
                    scored_chunks.append({
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_name": filename,
                        "subject_name": subject_name,
                        "collection_name": collection_name,
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "character_start": chunk.character_start,
                        "character_end": chunk.character_end,
                        "similarity": round(float(sim), 4),
                        "chunk_index": chunk.chunk_index,
                    })

            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            return scored_chunks[:top_k]
        except Exception:
            # Fallback to pure Python loop
            scored_chunks = []
            for chunk, filename, subject_name, collection_name in valid_rows:
                sim = self._cosine_similarity(query_embedding, chunk.embedding)
                if sim >= min_similarity:
                    scored_chunks.append({
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_name": filename,
                        "subject_name": subject_name,
                        "collection_name": collection_name,
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "character_start": chunk.character_start,
                        "character_end": chunk.character_end,
                        "similarity": round(float(sim), 4),
                        "chunk_index": chunk.chunk_index,
                    })
            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            return scored_chunks[:top_k]

    async def get_all_user_chunks_for_lexical(
        self,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        subject: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve user's chunks for hybrid keyword matching."""
        conditions = [
            DocumentChunk.user_id == user_id,
            Document.status != "failed",
        ]

        if document_ids:
            conditions.append(DocumentChunk.document_id.in_(document_ids))
        if subject:
            conditions.append(Document.subject_name == subject)
        if collection:
            conditions.append(Document.collection_name == collection)

        query = (
            select(DocumentChunk, Document.filename, Document.subject_name, Document.collection_name)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(and_(*conditions))
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_name": filename,
                "subject_name": subject_name,
                "collection_name": collection_name,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "character_start": chunk.character_start,
                "character_end": chunk.character_end,
                "chunk_index": chunk.chunk_index,
            }
            for chunk, filename, subject_name, collection_name in rows
        ]
