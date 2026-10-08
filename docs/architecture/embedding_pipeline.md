# Study Buddy — Embedding & Indexing Pipeline

## 1. Document Ingestion Integration

In Phase 3, the document ingestion pipeline from Phase 2 is extended with automatic batch embedding generation and indexing.

```text
Upload File
    ↓
Validation & Storage
    ↓
Text Extraction (pypdf / python-docx / txt / md)
    ↓
Sanitization & Cleaning
    ↓
Section Detection & Chunking
    ↓
Batch Embedding Generation  [Stage: EMBEDDING (75%)]
    ↓
Vector Store Indexing       [Stage: INDEXING  (90%)]
    ↓
Knowledge Base Ready        [Stage: READY    (100%)]
```

---

## 2. Ingestion Stages & Progress Tracking

| Stage | Progress | Description |
| :--- | :--- | :--- |
| `uploading` | 10% | Receiving raw file bytes on the server |
| `extracting` | 30% | Parsing native text and page structure |
| `cleaning` | 50% | Stripping control characters, normalizing whitespace |
| `chunking` | 65% | Semantic chunking with overlap (400–1000 chars) |
| `embedding` | 75% | Generating vector representations for all chunks |
| `indexing` | 90% | Persisting vectors into database with JSON/pgvector |
| `ready` | 100% | Available for hybrid search and grounded tutoring |
| `failed` | - | Failure recorded with readable `error_message` |

---

## 3. Batch Embedding Operations

To optimize performance, embeddings are generated in batches:

- Batch size: 32 chunks per call.
- Text content is prepended with section context: `f"Section: {chunk.section_title}\n{chunk.content}"` to improve semantic retrieval accuracy.
- Dimension verification: Chunks validate their vector dimension against the parent document's `embedding_dimension`.

---

## 4. Re-Indexing Pipeline (`POST /api/v1/documents/{document_id}/reindex`)

When a user switches embedding providers (e.g. from `local` to `gemini`) or after updating embedding dimensions, documents can be re-indexed without re-uploading the original file:

1. Retrieves existing chunks from the database.
2. Updates document status to `embedding_status = "indexing"`.
3. Re-embeds all chunk contents using the newly configured provider.
4. Overwrites chunk vectors and updates `embedding_model` and `embedded_at`.
5. Marks `embedding_status = "ready"`.

---

## 5. Fault Tolerance & Fallbacks

- If an external embedding API fails or times out, the document transitions to `embedding_status = "failed"`.
- The document's extracted text and chunks remain safe and intact.
- The student can retry indexing at any time via the UI retry button.
- Local fallback embeddings guarantee that basic search and tutoring work even during internet disruptions.
