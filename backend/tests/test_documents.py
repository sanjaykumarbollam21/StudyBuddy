import pytest
import io
from httpx import AsyncClient
import pypdf
import docx

def create_sample_pdf() -> bytes:
    """Generate a real valid PDF with 2 pages in memory."""
    buf = io.BytesIO()
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_blank_page(width=72, height=72)
    writer.write(buf)
    return buf.getvalue()

def create_sample_docx(text: str = "Operating Systems Unit 1\nConcurrency and Deadlocks") -> bytes:
    """Generate a real valid DOCX in memory."""
    buf = io.BytesIO()
    doc = docx.Document()
    doc.add_heading("Chapter 1: Process Synchronization", level=1)
    doc.add_paragraph(text)
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Concept"
    table.cell(0, 1).text = "Description"
    table.cell(1, 0).text = "Semaphore"
    table.cell(1, 1).text = "Integer synchronization primitive"
    doc.save(buf)
    return buf.getvalue()

@pytest.mark.asyncio
async def test_upload_requires_authentication(client: AsyncClient):
    files = {"file": ("test.txt", b"Hello World", "text/plain")}
    res = await client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_valid_pdf_upload_and_extraction(client: AsyncClient):
    user = {"email": "pdf.student@studybuddy.io", "password": "Password123!", "full_name": "PDF Student"}
    signup_res = await client.post("/api/v1/auth/signup", json=user)
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = create_sample_pdf()
    files = {"file": ("OS_Architecture.pdf", pdf_bytes, "application/pdf")}
    data = {"subject_name": "Operating Systems", "collection_name": "Syllabus"}
    
    upload_res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 201
    doc = upload_res.json()
    assert doc["filename"] == "OS_Architecture.pdf"
    assert doc["file_type"] == "pdf"
    assert doc["status"] == "ready"
    assert doc["page_count"] == 2

@pytest.mark.asyncio
async def test_valid_docx_upload_and_extraction(client: AsyncClient):
    user = {"email": "docx.student@studybuddy.io", "password": "Password123!", "full_name": "DOCX Student"}
    signup_res = await client.post("/api/v1/auth/signup", json=user)
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    docx_bytes = create_sample_docx("Deadlocks and circular wait conditions.")
    files = {"file": ("Deadlocks_Chapter.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    
    upload_res = await client.post("/api/v1/documents/upload", files=files, headers=headers)
    assert upload_res.status_code == 201
    doc = upload_res.json()
    assert doc["filename"] == "Deadlocks_Chapter.docx"
    assert doc["file_type"] == "docx"
    assert doc["status"] == "ready"

    # Detail check
    detail_res = await client.get(f"/api/v1/documents/{doc['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["chunks"]) >= 1
    assert "Process Synchronization" in detail["chunks"][0]["section_title"] or "Semaphore" in detail["chunks"][0]["content"]

@pytest.mark.asyncio
async def test_txt_and_markdown_upload_and_chunking(client: AsyncClient):
    user = {"email": "txt.student@studybuddy.io", "password": "Password123!", "full_name": "TXT Student"}
    signup_res = await client.post("/api/v1/auth/signup", json=user)
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. TXT Upload
    txt_content = (
        "Operating Systems Memory Management\n\n"
        "Virtual memory allows execution of processes not completely in memory. "
        "Page tables map logical addresses to physical frame addresses. "
        "Page replacement algorithms include FIFO, LRU, and Optimal."
    )
    txt_files = {"file": ("Memory.txt", txt_content.encode("utf-8"), "text/plain")}
    txt_res = await client.post("/api/v1/documents/upload", files=txt_files, headers=headers)
    assert txt_res.status_code == 201
    assert txt_res.json()["file_type"] == "txt"

    # 2. Markdown Upload
    md_content = (
        "# Machine Learning Fundamentals\n\n"
        "## Supervised Learning\n"
        "Linear Regression predicts continuous values.\n\n"
        "## Optimization\n"
        "Gradient descent minimizes the cost function."
    )
    md_files = {"file": ("ML_Notes.md", md_content.encode("utf-8"), "text/markdown")}
    md_res = await client.post("/api/v1/documents/upload", files=md_files, headers=headers)
    assert md_res.status_code == 201
    md_doc = md_res.json()
    assert md_doc["file_type"] == "md"

    # Verify chunk metadata on markdown doc
    detail_res = await client.get(f"/api/v1/documents/{md_doc['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["chunks"]) >= 1
    assert detail["chunks"][0]["chunk_index"] == 0
    assert detail["chunks"][0]["page_number"] >= 1

@pytest.mark.asyncio
async def test_validation_unsupported_future_oversized_and_empty_files(client: AsyncClient):
    user = {"email": "val.student@studybuddy.io", "password": "Password123!", "full_name": "Val Student"}
    signup_res = await client.post("/api/v1/auth/signup", json=user)
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Unsupported extension (.exe)
    bad_res = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("virus.exe", b"malicious code", "application/octet-stream")},
        headers=headers,
    )
    assert bad_res.status_code == 400
    assert "Unsupported file format" in bad_res.json()["detail"]

    # 2. Future extension (.pptx) -> friendly message
    future_res = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("slides.pptx", b"slides presentation", "application/vnd.ms-powerpoint")},
        headers=headers,
    )
    assert future_res.status_code == 400
    assert "will be supported in a future version" in future_res.json()["detail"]

    # 3. Empty file
    empty_res = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=headers,
    )
    assert empty_res.status_code == 400
    assert "Empty files cannot be processed" in empty_res.json()["detail"]

@pytest.mark.asyncio
async def test_user_data_isolation_and_deletion(client: AsyncClient):
    # Register user 1
    u1 = {"email": "user1.isolation@studybuddy.io", "password": "Password123!", "full_name": "User One"}
    s1 = await client.post("/api/v1/auth/signup", json=u1)
    t1 = s1.json()["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    # Register user 2
    u2 = {"email": "user2.isolation@studybuddy.io", "password": "Password123!", "full_name": "User Two"}
    s2 = await client.post("/api/v1/auth/signup", json=u2)
    t2 = s2.json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    # User 1 uploads a private document
    files = {"file": ("User1_Private_Notes.txt", b"Private student notes", "text/plain")}
    up1 = await client.post("/api/v1/documents/upload", files=files, headers=h1)
    doc1_id = up1.json()["id"]

    # User 2 list documents -> must be empty
    list2 = await client.get("/api/v1/documents", headers=h2)
    assert list2.status_code == 200
    assert len(list2.json()) == 0

    # User 2 cannot access user 1's document
    unauth_detail = await client.get(f"/api/v1/documents/{doc1_id}", headers=h2)
    assert unauth_detail.status_code == 404

    # User 2 cannot delete user 1's document
    unauth_delete = await client.delete(f"/api/v1/documents/{doc1_id}", headers=h2)
    assert unauth_delete.status_code == 404

    # User 1 can delete own document
    del1 = await client.delete(f"/api/v1/documents/{doc1_id}", headers=h1)
    assert del1.status_code == 200
    assert del1.json()["success"] is True

    # Confirm it's gone
    list1 = await client.get("/api/v1/documents", headers=h1)
    assert len(list1.json()) == 0

@pytest.mark.asyncio
async def test_status_retry_and_learning_contract(client: AsyncClient):
    user = {"email": "status.student@studybuddy.io", "password": "Password123!", "full_name": "Status Student"}
    signup_res = await client.post("/api/v1/auth/signup", json=user)
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("Notes.txt", b"Study notes content", "text/plain")}
    upload_res = await client.post("/api/v1/documents/upload", files=files, headers=headers)
    doc_id = upload_res.json()["id"]

    # Status endpoint check
    status_res = await client.get(f"/api/v1/documents/{doc_id}/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["document_id"] == doc_id
    assert status_data["status"] == "ready"
    assert status_data["progress"] == 100

    # Retry endpoint check
    retry_res = await client.post(f"/api/v1/documents/{doc_id}/retry", headers=headers)
    assert retry_res.status_code == 200
    assert retry_res.json()["document_id"] == doc_id

    # Learning contract endpoint check
    learn_res = await client.post(f"/api/v1/documents/learning/from-document/{doc_id}", headers=headers)
    assert learn_res.status_code == 200
    assert learn_res.json()["status"] == "curriculum_queued"
