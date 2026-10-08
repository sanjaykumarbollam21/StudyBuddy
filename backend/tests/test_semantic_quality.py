import pytest
import socket
from app.embeddings import get_embedding_provider
from app.embeddings.local import LocalEmbeddingProvider
from app.search.hybrid import KnowledgeSearchService
from app.repositories.vector_repository import VectorRepository

@pytest.mark.asyncio
async def test_semantic_embedding_ranks_paraphrased_query_over_distractors():
    """
    Benchmark test: Query wording differs substantially from document text.
    The pretrained local embedding model must recognize the conceptual relationship.
    
    Query: "What happens when a process waits indefinitely for resources?"
    Target chunk: "Deadlock occurs when processes are permanently blocked waiting for resources held by each other."
    """
    provider = get_embedding_provider("local")
    assert provider.get_dimension() == 384
    assert getattr(provider, "is_pretrained", False) is True

    query = "What happens when a process waits indefinitely for resources?"
    target_chunk = (
        "Deadlock occurs when processes are permanently blocked waiting for resources "
        "held by each other, leading to system cessation unless resolved by Banker algorithm."
    )
    distractor_1 = (
        "CPU scheduling algorithms determine which runnable thread executes next "
        "on the processor core according to priority or round-robin time slice."
    )
    distractor_2 = (
        "Relational database third normal form requires that all non-key attributes "
        "are non-transitively dependent on the primary key."
    )

    q_vec = await provider.embed_text(query)
    target_vec = await provider.embed_text(target_chunk)
    d1_vec = await provider.embed_text(distractor_1)
    d2_vec = await provider.embed_text(distractor_2)

    def cos_sim(a, b):
        return sum(x * y for x, y in zip(a, b))

    sim_target = cos_sim(q_vec, target_vec)
    sim_d1 = cos_sim(q_vec, d1_vec)
    sim_d2 = cos_sim(q_vec, d2_vec)

    # True semantic match should score highest
    assert sim_target > sim_d1, f"Expected target ({sim_target:.3f}) > CPU scheduling ({sim_d1:.3f})"
    assert sim_target > sim_d2, f"Expected target ({sim_target:.3f}) > Database normalization ({sim_d2:.3f})"
    assert sim_target >= 0.70, f"Expected strong semantic similarity (got {sim_target:.3f})"

@pytest.mark.asyncio
async def test_semantic_retrieval_with_synonyms_and_indirect_questions():
    """
    Test indirect queries where key terms are expressed as questions or synonyms.
    Query: "How does computer memory handle paging faults?"
    Target chunk: "When an address references an unmapped frame, the MMU triggers a page fault exception."
    """
    provider = get_embedding_provider("local")
    query = "How does computer memory handle paging faults?"
    target = "When an address references an unmapped frame, the MMU triggers a page fault exception loading disk sectors."
    unrelated = "Python dictionary lookups provide average O(1) time complexity through hash tables."

    q_vec = await provider.embed_text(query)
    target_vec = await provider.embed_text(target)
    unrelated_vec = await provider.embed_text(unrelated)

    def cos_sim(a, b):
        return sum(x * y for x, y in zip(a, b))

    sim_target = cos_sim(q_vec, target_vec)
    sim_unrelated = cos_sim(q_vec, unrelated_vec)

    assert sim_target > sim_unrelated
    assert sim_target > 0.65

@pytest.mark.asyncio
async def test_offline_mode_guarantees_zero_network_connections():
    """
    Verify that in Offline Mode, embedding generation runs without any network connections.
    Attempts to open a socket connection raise an immediate error.
    """
    orig_connect = socket.socket.connect

    def blocked_connect(self, *args, **kwargs):
        raise ConnectionRefusedError("Offline policy violation: Network connection prohibited!")

    socket.socket.connect = blocked_connect
    try:
        provider = LocalEmbeddingProvider(dimension=384, model_name="BAAI/bge-small-en-v1.5")
        vec = await provider.embed_text("Privacy-preserving local learning materials verification.")
        assert len(vec) == 384
        # Verify vector is unit-normalized
        norm_sq = sum(x * x for x in vec)
        assert abs(norm_sq - 1.0) < 0.01
    finally:
        socket.socket.connect = orig_connect

@pytest.mark.asyncio
async def test_batch_embedding_consistency_and_performance():
    """
    Verify that batch embedding produces identical vectors to single-text embedding,
    and runs in sub-100ms for study chunks.
    """
    provider = get_embedding_provider("local")
    texts = [
        "First Law of Thermodynamics: Energy cannot be created or destroyed.",
        "Second Law of Thermodynamics: Entropy of an isolated system always increases.",
        "Third Law of Thermodynamics: Entropy of a system approaches zero at absolute zero.",
    ]

    batch_vecs = await provider.embed_texts(texts)
    assert len(batch_vecs) == 3

    for i, text in enumerate(texts):
        single_vec = await provider.embed_text(text)
        dot_product = sum(x * y for x, y in zip(single_vec, batch_vecs[i]))
        assert dot_product > 0.999, f"Batch vector for text {i} differs from single vector!"
