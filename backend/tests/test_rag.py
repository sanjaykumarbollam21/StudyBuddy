import pytest
from httpx import AsyncClient
from app.embeddings import get_embedding_provider
from app.embeddings.local import LocalEmbeddingProvider
from app.search.context_builder import RAGContextBuilder
from app.tutor.grounding import STRICT_MATERIALS_FALLBACK
from app.schemas.tutor import GroundingMode

@pytest.mark.asyncio
async def test_embedding_provider_and_dimension():
    provider = LocalEmbeddingProvider(dimension=384, model_name="local-test-384")
    assert provider.get_dimension() == 384
    assert provider.get_model_name() == "local-test-384"

    text = "Operating systems manage CPU scheduling and virtual memory."
    vec = await provider.embed_text(text)
    assert len(vec) == 384
    # Check that vector is non-zero
    assert any(v != 0.0 for v in vec)

    # Empty text returns zero vector
    empty_vec = await provider.embed_text("")
    assert len(empty_vec) == 384
    assert all(v == 0.0 for v in empty_vec)

@pytest.mark.asyncio
async def test_batch_embedding():
    provider = get_embedding_provider("local")
    texts = [
        "First batch text on process synchronization.",
        "Second batch text on relational databases and SQL.",
        "Third batch text on gradient descent optimization."
    ]
    vectors = await provider.embed_texts(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == provider.get_dimension()

@pytest.mark.asyncio
async def test_context_builder_and_source_citations():
    builder = RAGContextBuilder(max_context_chars=4000)
    fake_chunks = [
        {
            "chunk_id": "c-1",
            "document_id": "doc-os",
            "document_name": "Operating_Systems.pdf",
            "page_number": 12,
            "section_title": "CPU Scheduling",
            "similarity": 0.94,
            "content": "Round Robin assigns equal time slices to each process."
        },
        {
            "chunk_id": "c-2",
            "document_id": "doc-os",
            "document_name": "Operating_Systems.pdf",
            "page_number": 15,
            "section_title": "Deadlock Avoidance",
            "similarity": 0.88,
            "content": "Banker's algorithm tests for safety state before allocation."
        }
    ]

    ctx = builder.build_context(fake_chunks)
    assert ctx.chunk_count == 2
    assert "Round Robin" in ctx.formatted_context
    assert "Banker's algorithm" in ctx.formatted_context
    assert len(ctx.citations) == 2
    assert ctx.citations[0].document_name == "Operating_Systems.pdf"
    assert ctx.citations[0].page_number == 12
    assert ctx.citations[0].section_title == "CPU Scheduling"

@pytest.mark.asyncio
async def test_semantic_and_hybrid_search_end_to_end(client: AsyncClient):
    # 1. Register student and login
    signup_resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "rag_student@example.com", "password": "SecurePassword123!", "full_name": "RAG Student"},
    )
    assert signup_resp.status_code == 201
    token = signup_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload study material
    os_md_content = b"""# Chapter 4: CPU Scheduling Algorithms

## 4.1 First-Come First-Served (FCFS)
The simplest scheduling algorithm is FCFS. Processes are dispatched in arrival order.

## 4.2 Round Robin (RR)
RR allocates a fixed time quantum to each ready process in turn.

## 4.3 Multilevel Feedback Queues
Separates processes into categories according to their CPU burst behavior.
"""
    files = {"file": ("OS_Scheduling_Notes.md", os_md_content, "text/markdown")}
    data = {"subject_name": "Operating Systems", "collection_name": "Unit 2"}
    upload_resp = await client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    # 3. Query Semantic Search
    sem_resp = await client.post(
        "/api/v1/search/semantic",
        headers=headers,
        json={"query": "time quantum round robin algorithms", "top_k": 5},
    )
    assert sem_resp.status_code == 200
    sem_data = sem_resp.json()
    assert sem_data["total_results"] > 0
    top_result = sem_data["results"][0]
    assert top_result["document_id"] == doc_id
    assert top_result["document_name"] == "OS_Scheduling_Notes.md"
    assert "Round Robin" in top_result["content"] or "quantum" in top_result["content"]

    # 4. Query Hybrid Search with subject filter
    hybrid_resp = await client.post(
        "/api/v1/search/hybrid",
        headers=headers,
        json={
            "query": "FCFS arrival order",
            "top_k": 3,
            "subject": "Operating Systems",
            "alpha": 0.6,
        },
    )
    assert hybrid_resp.status_code == 200
    hybrid_data = hybrid_resp.json()
    assert hybrid_data["total_results"] > 0
    assert "FCFS" in hybrid_data["results"][0]["content"]

@pytest.mark.asyncio
async def test_user_cannot_retrieve_other_users_chunks_and_deletion_removes_from_search(client: AsyncClient):
    # 1. Register User A and upload confidential document
    signup_a = await client.post(
        "/api/v1/auth/signup",
        json={"email": "alice_rag@example.com", "password": "Password123!", "full_name": "Alice RAG"},
    )
    token_a = signup_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    alice_content = b"Alice Secret Research on Distributed Paxos Consensus Protocol."
    files = {"file": ("Alice_Paxos.txt", alice_content, "text/plain")}
    upload_a = await client.post("/api/v1/documents/upload", headers=headers_a, files=files, data={"subject_name": "Distributed Systems"})
    assert upload_a.status_code == 201
    doc_a_id = upload_a.json()["id"]

    # 2. Register User B
    signup_b = await client.post(
        "/api/v1/auth/signup",
        json={"email": "bob_rag@example.com", "password": "Password123!", "full_name": "Bob RAG"},
    )
    token_b = signup_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B searches for Alice's exact keywords -> Must return ZERO results
    search_b = await client.post(
        "/api/v1/search/semantic",
        headers=headers_b,
        json={"query": "Paxos Consensus Protocol", "top_k": 5},
    )
    assert search_b.status_code == 200
    assert search_b.json()["total_results"] == 0

    # User B attempting to scope search to Alice's document ID -> Must return ZERO results
    scoped_b = await client.post(
        "/api/v1/search/hybrid",
        headers=headers_b,
        json={"query": "Paxos Consensus", "document_ids": [doc_a_id]},
    )
    assert scoped_b.status_code == 200
    assert scoped_b.json()["total_results"] == 0

    # 4. Alice can search her document
    search_a = await client.post(
        "/api/v1/search/semantic",
        headers=headers_a,
        json={"query": "Paxos Consensus Protocol", "top_k": 5},
    )
    assert search_a.status_code == 200
    assert search_a.json()["total_results"] > 0

    # 5. Delete Alice's document
    del_resp = await client.delete(f"/api/v1/documents/{doc_a_id}", headers=headers_a)
    assert del_resp.status_code == 200

    # 6. Verify Alice can NO LONGER retrieve chunks from the deleted document
    search_a_after = await client.post(
        "/api/v1/search/semantic",
        headers=headers_a,
        json={"query": "Paxos Consensus Protocol", "top_k": 5},
    )
    assert search_a_after.status_code == 200
    assert search_a_after.json()["total_results"] == 0

@pytest.mark.asyncio
async def test_tutor_grounded_response_and_anti_hallucination_modes(client: AsyncClient):
    # 1. Register student
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "tutor_student@example.com", "password": "Password123!", "full_name": "Tutor Student"},
    )
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload notes
    doc_content = b"""# Database Transactions & ACID
ACID stands for Atomicity, Consistency, Isolation, and Durability.
Two-Phase Locking (2PL) guarantees serializability by growing and shrinking lock phases.
"""
    files = {"file": ("DBMS_Transactions.txt", doc_content, "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=headers, files=files, data={"subject_name": "Databases"})
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    # 3. Test MATERIALS_PLUS_GENERAL mode
    ask_resp = await client.post(
        "/api/v1/tutor/ask",
        headers=headers,
        json={
            "query": "Explain Two-Phase Locking and ACID",
            "grounding_mode": "materials_plus_general",
        },
    )
    assert ask_resp.status_code == 200
    ask_data = ask_resp.json()
    assert ask_data["context_used"] is True
    assert len(ask_data["sources"]) > 0
    assert ask_data["sources"][0]["document_name"] == "DBMS_Transactions.txt"
    assert "Two-Phase Locking" in ask_data["answer"] or "ACID" in ask_data["answer"]

    # 4. Test STRICT_MATERIALS mode with unrelated question not in notes -> Must trigger Anti-Hallucination Fallback
    strict_unrelated = await client.post(
        "/api/v1/tutor/ask",
        headers=headers,
        json={
            "query": "Explain Quantum Entanglement and Bell's Theorem",
            "grounding_mode": "strict_materials",
            "document_ids": [doc_id],
        },
    )
    assert strict_unrelated.status_code == 200
    strict_data = strict_unrelated.json()
    assert STRICT_MATERIALS_FALLBACK in strict_data["answer"]
    assert strict_data["context_used"] is False

    # 5. Test "Teach Me This" Document Session endpoint
    session_resp = await client.post(f"/api/v1/tutor/document-session/{doc_id}", headers=headers)
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    assert session_data["document_id"] == doc_id
    assert session_data["document_name"] == "DBMS_Transactions.txt"
    assert len(session_data["suggested_topics"]) > 0

@pytest.mark.asyncio
async def test_reindex_document_pipeline(client: AsyncClient):
    # 1. Register student
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "reindex_user@example.com", "password": "Password123!", "full_name": "Reindex User"},
    )
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload document
    files = {"file": ("Network_Protocols.txt", b"TCP provides reliable, ordered byte streams. UDP is connectionless.", "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=headers, files=files)
    doc_id = upload.json()["id"]

    # 3. Trigger reindex
    reindex_resp = await client.post(f"/api/v1/documents/{doc_id}/reindex", headers=headers)
    assert reindex_resp.status_code == 200
    reindex_data = reindex_resp.json()
    assert reindex_data["status"] == "ready"
    assert reindex_data["chunks_embedded"] > 0
    assert reindex_data["dimension"] == 384
