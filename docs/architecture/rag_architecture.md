# Study Buddy — Phase 3: RAG & Retrieval Architecture

## 1. Overview & Core Philosophy

Study Buddy is architected as an **offline-first, provider-independent** personal learning system. A student's personal notes, textbooks, and syllabus can be indexed, retrieved, and taught without requiring active internet connectivity or paid external API keys.

```text
                             STUDY BUDDY
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
           LOCAL AI (Offline)               ONLINE AI (Cloud)
                 │                                 │
         ┌───────┴───────┐                 ┌───────┴───────┐
         │               │                 │               │
     Local LLM      Local Embeds       Cloud LLM      Cloud Embeds
     (quantized)     (feature proj)    (Gemini/Ollama) (Gemini/OpenAI)
         │               │                 │               │
         └───────┬───────┘                 └───────┬───────┘
                 │                                 │
                 └────────────────┬────────────────┘
                                  ↓
                        Hybrid Knowledge Search
                                  ↓
                        Grounded AI Teacher
```

---

## 2. Operating Modes

| Mode | Embeddings | Vector Search | LLM Generation | Internet Required | Privacy Guarantee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Offline Mode** 🟢 | Pretrained local ONNX (`bge-small-en-v1.5`) | In-memory / pgvector local | Local quantized / Mock tutor | No | 100% On-device / Local server |
| **Hybrid Mode** 🟣 (Recommended) | Pretrained local ONNX (`bge-small-en-v1.5`) | In-memory / pgvector local | Local RAG + optional cloud reasoning | Only for complex cloud LLM queries | Documents stay local; search is offline |
| **Online Mode** 🔵 | Gemini / OpenAI | pgvector / Cloud vector DB | Gemini 1.5 Pro / GPT-4o | Yes | Standard API guarantees |

---

## 3. Provider-Independent Embedding Abstraction

Vectors are **never hardcoded to dimension 768**. The dimension is dynamically determined by the active provider:

```python
class EmbeddingProvider(ABC):
    @abstractmethod
    def get_dimension(self) -> int: ...

    @abstractmethod
    def get_model_name(self) -> str: ...

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
```

### Supported Providers:
1. **`LocalEmbeddingProvider`** (Upgraded in Phase 3.1):
   - **Primary Model**: Pretrained ONNX-quantized `BAAI/bge-small-en-v1.5` (384 dimensions) running via CPU-optimized `fastembed` with vectorized batch processing.
   - **True Semantic Understanding**: Accurately maps conceptual relationships, synonyms, and paraphrased questions (e.g., query *"What happens when a process waits indefinitely for resources?"* $\to$ target chunk *"Deadlock occurs when processes are permanently blocked waiting for resources..."* with cosine similarity $> 0.83$).
   - **Zero Network Guarantee**: Runs entirely on cached local weights with network connectivity disabled; zero document contents leave the machine.
   - **Robust Fallback**: Gracefully falls back to deterministic feature projection if ONNX libraries are missing in an environment.
2. **`GeminiEmbeddingProvider`**:
   - `text-embedding-004` (768 dimensions) via Google GenAI SDK.
3. **`OpenAIEmbeddingProvider`**:
   - `text-embedding-3-small` (1536 dimensions) or `text-embedding-3-large` (3072 dimensions).

---

## 4. Multi-Tenant Vector Isolation

Security and student privacy are strictly enforced at the database and repository layers:

```python
# Every vector search strictly enforces the user filter:
query = select(DocumentChunk).join(Document).where(
    Document.user_id == user_id,
    Document.status == "ready",
    DocumentChunk.embedding.isnot(None)
)
```

- Cross-tenant retrieval is architecturally impossible.
- Soft or hard deletion of a document immediately purges its chunks and vectors from all search indices.

---

## 5. Hybrid Retrieval Engine

Dense semantic similarity alone can miss exact technical identifiers (e.g., *TCP*, *SQL*, *ACID*, *LRU*, *Dijkstra*). The Study Buddy search engine combines dense vector cosine similarity with lexical keyword matching:

$$\text{Final Score} = \alpha \cdot \text{Cosine Sim} + (1 - \alpha) \cdot \text{BM25 / Keyword Score}$$

- **Query Normalization**: Trims punctuation, collapses whitespace, extracts key technical terms.
- **Result Diversification**: Groups adjacent chunks from the same section to ensure diverse learning context.
- **Configurable Alpha**: Defaults to $\alpha = 0.70$ (70% semantic, 30% exact keyword match).

---

## 6. Grounding Modes & Anti-Hallucination Guardrails

Study Buddy prevents hallucinated teaching through three explicit grounding modes:

1. **`strict_materials`**:
   - Answers *only* from the retrieved student documents.
   - If retrieved chunk similarity falls below `SIMILARITY_THRESHOLD` (default 0.35), refuses to hallucinate:
     > *"I couldn't find information about this topic in your saved study materials. Would you like me to answer using general knowledge or help you research this topic?"*
2. **`materials_plus_general`** (Default):
   - Grounds core definitions and equations in the student's materials.
   - Uses general knowledge only for analogies, intuitive examples, and follow-up guidance.
   - Every claim grounded in materials carries an authentic source citation.
3. **`general`**:
   - Allows open tutoring when the student has not uploaded materials for the topic.

---

## 7. Authentic Source Citations

Every grounded response includes clickable source citations linking directly to the student's uploaded material:

```json
{
  "document_id": "0194...",
  "document_name": "Operating_Systems_Unit_2.pdf",
  "page_number": 14,
  "section_title": "Deadlock Characterization",
  "similarity": 0.892,
  "snippet": "A deadlock condition requires four Coffman conditions: Mutual Exclusion, Hold and Wait..."
}
```
