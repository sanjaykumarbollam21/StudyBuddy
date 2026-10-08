# Study Buddy — Document Processing Pipeline & Personal Knowledge Base

## 1. Overview
The **Document Processing Pipeline** provides a reliable, secure, and permanent knowledge base foundation for the Study Buddy personal AI teacher. When students upload study materials (textbooks, lecture slides, notes, syllabi), the system stores them securely, extracts structured text while preserving document hierarchy, cleans artifacts, detects sections, and divides text into semantic chunks ready for Phase 3 vector embeddings and RAG tutoring.

---

## 2. Architecture & Data Flow

```text
Student (Mobile / Web / Desktop)
   │
   ▼
Frontend Materials Tab (FilePicker / Multi-File Queue)
   │ Multipart POST /api/v1/documents/upload
   ▼
FastAPI API Layer (Security & JWT Auth Verification)
   │
   ├── Storage Provider (Isolated directory: storage/users/{user_id}/documents/)
   │   └── SHA256 filename generation & Path traversal protection
   │
   ├── Document Record Created (status: UPLOADING -> PROCESSING)
   │
   ▼
DocumentProcessor Pipeline:
   │
   ├── 1. Text Extraction (PDFExtractor / DOCXExtractor / TXTExtractor / MarkdownExtractor)
   │      - PDF: Page boundary tracking, pypdf text extraction, OCR fallback detection
   │      - DOCX: Paragraphs, heading levels (1-6), bulleted lists, structured tables
   │      - TXT / Markdown: Normalized line endings, markdown headers (#, ##, ###)
   │
   ├── 2. Text Cleaning Pipeline (TextCleaner)
   │      - Unicode NFKC normalization
   │      - Repeated whitespace and broken hyphen line-wrap fixing
   │      - Header/footer artifact removal
   │
   ├── 3. Section Detection (SectionDetector)
   │      - Hierarchical chapter/section tree detection
   │      - Character start/end boundary indexing
   │
   ├── 4. Semantic Chunking (SemanticChunker)
   │      - Sentence-boundary aware windowing (configurable chunk size & overlap)
   │      - Metadata injection: document_id, user_id, page_number, section_title
   │
   ▼
Database Persistence (SQLAlchemy AsyncSession)
   ├── documents record updated (status: READY, progress: 100%, stage: ready)
   └── document_chunks batch inserted
```

---

## 3. Supported File Formats

| Format | Extension | Extractor | Features & Capabilities |
| :--- | :--- | :--- | :--- |
| **PDF** | `.pdf` | `PDFExtractor` (`pypdf`) | Page-by-page extraction, page numbering preserved, empty text scanned-detection (`needs_ocr: true`). |
| **Word DOCX** | `.docx` | `DOCXExtractor` (`python-docx`) | Heading styles (1–6), paragraphs, bullet/numbered lists, table cell extraction. |
| **Plain Text** | `.txt` | `TXTExtractor` | UTF-8 normalization, paragraph detection, line break correction. |
| **Markdown** | `.md`, `.markdown` | `MarkdownExtractor` | Heading hierarchy parsing (`#`, `##`), list preservation, code block protection. |
| *Future Formats* | `.ppt`, `.pptx`, `.csv`, `.png`, `.jpg` | *Roadmap* | Returns user-facing notification: `"This file type will be supported in a future version."` |

---

## 4. Processing State Machine

```text
UPLOADING
    ↓
UPLOADED
    ↓
PROCESSING
    ↓
EXTRACTING
    ↓
CLEANING
    ↓
CHUNKING
    ↓
INDEXING
    ↓
READY
```

### Failure & Recovery State
```text
ANY_STATE ────(Exception)────> FAILED ────(POST /retry)────> RETRY / PROCESSING
```
- Failures store internal logs without exposing sensitive server stack traces to students.
- Retry endpoint allows students or background workers to re-run processing seamlessly.

---

## 5. Storage Architecture & User Isolation

- **Storage Provider Interface**: `StorageProvider` abstract base class with `LocalStorageProvider` and cloud-ready design.
- **Root Path**: `storage/users/{user_id}/documents/{safe_filename}`
- **Security Protections**:
  - Path traversal checks: Uploaded filenames are scrubbed with `Path(filename).name` and stored using unique UUIDs.
  - Ownership enforcement: Every query explicitly filters on `user_id == current_user.id`.
  - Zero cross-tenant leakage: Attempts to fetch, status check, retry, or delete another student's document return `404 Not Found`.

---

## 6. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Multipart file upload with subject/collection metadata. Validates file size (50MB max) and MIME type. |
| `GET` | `/api/v1/documents` | Lists all saved materials for the user. Supports `status`, `subject`, and `search` query filters. |
| `GET` | `/api/v1/documents/{document_id}` | Returns full document details, metrics, chunk hierarchy, and extracted text preview. |
| `GET` | `/api/v1/documents/{document_id}/status` | Lightweight status polling (`status`, `progress`, `stage`, `message`). |
| `POST` | `/api/v1/documents/{document_id}/retry` | Re-triggers document processing pipeline for failed documents. |
| `DELETE` | `/api/v1/documents/{document_id}` | Permanently removes document, physical file, and all associated chunks. |
| `POST` | `/api/v1/documents/bulk-delete` | Batch deletes multiple selected documents and chunks in one request. |
| `POST` | `/api/v1/documents/learning/from-document/{document_id}` | Contract endpoint preparing for AI Teacher curriculum and lesson generation. |

---

## 7. Database Entities

### `documents`
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key referencing `users.id`)
- `filename`, `original_filename` (VARCHAR)
- `file_type`, `mime_type` (VARCHAR)
- `file_size_bytes` (BIGINT)
- `storage_path` (VARCHAR)
- `status` (`ready`, `processing`, `failed`, etc.)
- `processing_stage` (`extracting`, `cleaning`, `chunking`, `indexing`, `ready`)
- `progress` (INTEGER, 0–100)
- `page_count`, `extracted_character_count`, `section_count`, `chunk_count`
- `subject_name`, `collection_name`
- `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE)

### `document_chunks`
- `id` (UUID, primary key)
- `document_id` (UUID, foreign key referencing `documents.id`)
- `user_id` (UUID, foreign key referencing `users.id`)
- `chunk_index` (INTEGER)
- `content` (TEXT)
- `page_number` (INTEGER, optional)
- `section_title` (VARCHAR, optional)
- `character_start`, `character_end` (INTEGER)
- `embedding` (VECTOR(768), pgvector column ready for Phase 3)
- `created_at` (TIMESTAMP WITH TIME ZONE)

---

## 8. Frontend Implementation

1. **Materials Tab (`MaterialsTab`)**:
   - Header with total document count and permanent retention indicator.
   - Native File Picker via `file_picker` package supporting multi-file selection.
   - Upload Queue widget showing live stage indicators (`Processing 68%`, `Extracting`, `Ready`, `Failed`).
   - Status filters (`All`, `Ready`, `Processing`, `Failed`) and Subject Collection filter chips.
   - Multi-select batch mode with checkbox toggles and "Delete Selected" bulk operation.
2. **Document Details & Reader Screen (`DocumentDetailScreen`)**:
   - Comprehensive metadata banner: pages, file size, character count, section count, chunk count.
   - Extracted text reader displaying normalized document content.
   - Semantic chunk explorer showing chunk index, page numbers, and section headers.
   - "Teach Me This" action integrated directly with `TutorSheet`.
