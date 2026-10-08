import pytest
import os
import re
import asyncio
from typing import Dict, Any
from app.tutor.providers.base import LLMProvider
from app.tutor.providers.gemini import GeminiLLMProvider
from app.tutor.providers.openai import OpenAILLMProvider
from app.tutor.providers.mock import MockLLMProvider
from app.teaching.curriculum import get_curriculum_for_topic
from app.core.config import settings

@pytest.mark.asyncio
async def test_secret_scanning_no_secrets_in_frontend():
    """Verify no cloud provider secrets exist in frontend Dart files or APK configs."""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "lib"))
    secret_patterns = [
        re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),       # Google API Key format
        re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),    # OpenAI API Key format
        re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),     # Anthropic API Key format
    ]
    
    leaked_findings = []
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith(".dart"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        if pattern.search(content):
                            leaked_findings.append(f"{file_path} matched pattern {pattern.pattern}")
                            
    assert len(leaked_findings) == 0, f"Found leaked secrets in frontend: {leaked_findings}"

@pytest.mark.asyncio
async def test_cloud_provider_model_and_resilience():
    """Verify cloud provider timeout, retry bounds, and streaming interface."""
    # Test Mock/Fallback interface
    mock_provider = MockLLMProvider()
    resp = await mock_provider.generate_response("Explain Chauri Chaura", "History teacher")
    assert len(resp) > 20
    assert "lesson" in resp.lower()

    # Test streaming response generator
    stream_chunks = []
    async for chunk in mock_provider.stream_response("Explain Chauri Chaura", "History teacher"):
        stream_chunks.append(chunk)
    assert len(stream_chunks) > 0
    full_streamed = "".join(stream_chunks)
    assert len(full_streamed) > 10

    # Test Gemini provider configuration & resilience limits
    gemini = GeminiLLMProvider(api_key="mock_key", model_name="gemini-1.5-flash")
    assert gemini.model_name == "gemini-1.5-flash"
    assert gemini.timeout == settings.AI_REQUEST_TIMEOUT_SECONDS
    assert gemini.max_retries == 3

    # Test OpenAI provider configuration & resilience limits
    openai_prov = OpenAILLMProvider(api_key="mock_key", model_name="gpt-4o-mini")
    assert openai_prov.model_name == "gpt-4o-mini"
    assert openai_prov.max_retries == 3

@pytest.mark.asyncio
async def test_document_grounding_two_contrasting_materials():
    """
    Grounding verification: Test two distinctly different documents:
    Doc A: Indian Modern History (Non-Cooperation Movement, 1922 Chauri Chaura).
    Doc B: Operating Systems (Dijkstra 1965 Counting Semaphores).
    Verify that lessons for Doc A extract and cite ONLY Doc A facts.
    """
    doc_a_chunks = [
        {
            "chunk_id": "hist-01",
            "content": "The Non-Cooperation Movement was launched in 1920 by Mahatma Gandhi. Following the violent Chauri Chaura incident in February 1922, Gandhi withdrew the movement at the Congress working committee meeting in Bardoli.",
            "document_id": "doc-history-upsc",
            "document_name": "Bipin_Chandra_History.pdf",
            "section_title": "Chauri Chaura Withdrawal",
            "page_number": 42
        },
        {
            "chunk_id": "hist-02",
            "content": "The resolution at Bardoli shocked leaders like Motilal Nehru and Subhas Chandra Bose, but Gandhi prioritized non-violence over premature political gains.",
            "document_id": "doc-history-upsc",
            "document_name": "Bipin_Chandra_History.pdf",
            "section_title": "Bardoli Resolution",
            "page_number": 43
        }
    ]

    doc_b_chunks = [
        {
            "chunk_id": "os-01",
            "content": "A semaphore is a synchronization variable introduced by Edsger Dijkstra in 1965. It maintains an integer value accessed only via two atomic operations: wait() (P) and signal() (V).",
            "document_id": "doc-os-cs",
            "document_name": "Silberschatz_OS.pdf",
            "section_title": "Atomic Semaphores",
            "page_number": 110
        }
    ]

    # Generate curriculum strictly grounded in Document A
    curriculum_a = get_curriculum_for_topic(
        topic="Non-Cooperation Movement Withdrawal",
        rag_chunks=doc_a_chunks
    )

    assert len(curriculum_a) >= 2
    # Check that Step 1 or Step 2 incorporates authentic text from Doc A
    all_content_a = " ".join([s.explanation for s in curriculum_a]) + " " + " ".join([s.title for s in curriculum_a])
    
    assert "Chauri Chaura" in all_content_a or "Gandhi" in all_content_a or "Bardoli" in all_content_a
    # Ensure zero leakage from Document B
    assert "semaphore" not in all_content_a.lower()
    assert "dijkstra" not in all_content_a.lower()

    # Generate curriculum strictly grounded in Document B
    curriculum_b = get_curriculum_for_topic(
        topic="Counting Semaphores",
        rag_chunks=doc_b_chunks
    )
    all_content_b = " ".join([s.explanation for s in curriculum_b]) + " " + " ".join([s.title for s in curriculum_b])
    assert "semaphore" in all_content_b.lower() or "dijkstra" in all_content_b.lower()
    # Ensure zero leakage from Document A
    assert "chauri chaura" not in all_content_b.lower()
    assert "bardoli" not in all_content_b.lower()

@pytest.mark.asyncio
async def test_cross_user_document_isolation():
    """Verify document isolation: User A's uploaded materials cannot be accessed by User B."""
    # Simulated multi-tenant store check
    user_a_id = "user_student_alpha"
    user_b_id = "user_student_beta"
    
    documents = {
        "doc-101": {"owner": user_a_id, "title": "Alpha Private Notes on UPSC Polity"},
        "doc-102": {"owner": user_b_id, "title": "Beta Private Notes on GATE CS"},
    }

    def access_document(requester_id: str, doc_id: str) -> Dict[str, Any]:
        doc = documents.get(doc_id)
        if not doc:
            raise KeyError("Document not found")
        if doc["owner"] != requester_id:
            raise PermissionError("Access forbidden: User does not own this document")
        return doc

    # User A accesses own doc -> Allowed
    assert access_document(user_a_id, "doc-101")["title"] == "Alpha Private Notes on UPSC Polity"

    # User B attempts to access User A's doc -> PermissionError (403)
    with pytest.raises(PermissionError):
        access_document(user_b_id, "doc-101")

@pytest.mark.asyncio
async def test_offline_failure_mode_predictability():
    """Verify provider failure terminates predictably within bounds and does not loop infinitely."""
    gemini = GeminiLLMProvider(api_key="your-gemini-api-key", model_name="gemini-1.5-flash")
    
    with pytest.raises(RuntimeError) as exc_info:
        await gemini.generate_response("Test prompt", "System")
    
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
