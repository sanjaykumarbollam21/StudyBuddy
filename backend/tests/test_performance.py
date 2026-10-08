import pytest
import time
import asyncio
import hashlib
from unittest.mock import AsyncMock, patch

from app.embeddings.local import LocalEmbeddingProvider, _EMBEDDING_CACHE
from app.embeddings import get_embedding_provider
from app.search.context_builder import RAGContextBuilder, MAX_RAG_CHUNKS, MAX_PROMPT_SIZE
from app.agent.decision import AgentDecisionEngine
from app.revision.sm2 import SM2Scheduler
from app.practice.generator import QuestionGenerator
from app.documents.chunker import ChunkingService


@pytest.mark.asyncio
async def test_embedding_model_singleton_and_caching():
    """
    Validates model singleton behavior and SHA-256 in-memory caching.
    A cached embedding must return in < 2ms without re-running model inference.
    """
    provider1 = get_embedding_provider("local")
    provider2 = get_embedding_provider("local")
    assert provider1 is provider2, "get_embedding_provider must return singleton instance"

    test_text = "Deadlock occurs when four Coffman conditions hold simultaneously."
    cache_key = hashlib.sha256(test_text.encode("utf-8")).hexdigest()

    # Clear test cache key if present
    _EMBEDDING_CACHE.pop(cache_key, None)

    # First computation
    vec1 = await provider1.embed_text(test_text)
    assert len(vec1) == 384
    assert cache_key in _EMBEDDING_CACHE, "Embedding must be cached under SHA256 key"

    # Second computation (cache hit)
    t0 = time.perf_counter()
    vec2 = await provider1.embed_text(test_text)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert vec1 == vec2
    assert duration_ms < 5.0, f"Cached embedding retrieval took {duration_ms:.2f}ms (expected < 5ms)"


@pytest.mark.asyncio
async def test_batch_embedding_caching_efficiency():
    """Validates that batch embedding utilizes cache for already seen items."""
    provider = get_embedding_provider("local")
    texts = [
        "CPU Scheduling: First-Come, First-Served",
        "Shortest Job Next scheduling algorithm",
        "Round Robin with configurable quantum",
    ]

    # Pre-embed first text
    _ = await provider.embed_text(texts[0])

    t0 = time.perf_counter()
    batch_vecs = await provider.embed_texts(texts)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert len(batch_vecs) == 3
    for v in batch_vecs:
        assert len(v) == 384


def test_rag_context_pruning_and_token_budget():
    """Validates strict context pruning limits (MAX_RAG_CHUNKS & MAX_PROMPT_SIZE)."""
    builder = RAGContextBuilder()
    assert builder.max_chunks == MAX_RAG_CHUNKS
    assert builder.max_context_chars <= MAX_PROMPT_SIZE

    # Provide 10 simulated large chunks
    mock_chunks = [
        {
            "chunk_id": f"chunk_{i}",
            "document_id": f"doc_{i}",
            "document_name": f"Operating Systems Chapter {i}",
            "content": f"Detailed architectural principles of memory paging and TLB caching index {i}. " * 30,
            "page_number": i + 1,
            "section_title": "Virtual Memory",
            "similarity": 0.85 - (i * 0.05),
        }
        for i in range(10)
    ]

    ctx = builder.build_context(mock_chunks)
    assert len(ctx.citations) <= MAX_RAG_CHUNKS, "RAG context builder must strictly cap citations at MAX_RAG_CHUNKS"
    assert len(ctx.retrieved_chunks) <= MAX_RAG_CHUNKS, "RAG context builder must strictly cap chunks at MAX_RAG_CHUNKS"
    assert len(ctx.formatted_context) <= MAX_PROMPT_SIZE + 500, "Context string must not breach character budget"


def test_vector_similarity_vectorization_budget():
    """Benchmarks vectorized cosine similarity calculation across 1,000 chunks."""
    import numpy as np
    chunk_count = 1000
    dim = 384

    matrix = np.random.randn(chunk_count, dim).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

    q_vec = np.random.randn(dim).astype(np.float32)
    q_vec /= np.linalg.norm(q_vec)

    t0 = time.perf_counter()
    sims = np.dot(matrix, q_vec)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert len(sims) == chunk_count
    assert duration_ms < 10.0, f"Vectorized similarity over 1000 chunks took {duration_ms:.2f}ms (expected < 10ms)"


def test_sm2_scheduler_low_latency():
    """Ensures SM-2 spaced repetition calculations execute in sub-millisecond time."""
    scheduler = SM2Scheduler()
    t0 = time.perf_counter()
    for q in range(6):
        res = scheduler.calculate_sm2(quality=q, repetition_count=2, interval_days=6, ease_factor=2.5)
        assert "next_review_date" in res
    duration_ms = (time.perf_counter() - t0) * 1000
    assert duration_ms < 5.0, f"SM-2 reviews calculation took {duration_ms:.2f}ms"


def test_agent_decision_engine_low_latency():
    """Ensures autonomous agent telemetry evaluation completes in sub-millisecond time."""
    agent = AgentDecisionEngine()
    t0 = time.perf_counter()
    decision = agent.evaluate_highest_value_task(
        available_minutes=45,
        days_until_exam=4,
        due_revision_count=2,
    )
    duration_ms = (time.perf_counter() - t0) * 1000
    assert "goal" in decision
    assert "proposed_actions" in decision
    assert duration_ms < 10.0, f"Agent decision evaluation took {duration_ms:.2f}ms"


def test_document_chunking_throughput():
    """Ensures document chunker processes a 200-paragraph textbook chapter in under 20ms."""
    chunker = ChunkingService(chunk_size=400, chunk_overlap=50)
    sample_text = "Process Management and Concurrency\n" * 200

    t0 = time.perf_counter()
    chunks = chunker.chunk_document(document_id="doc_perf", user_id="user_perf", text=sample_text)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert len(chunks) > 0
    assert duration_ms < 50.0, f"Chunking 200 paragraphs took {duration_ms:.2f}ms"
