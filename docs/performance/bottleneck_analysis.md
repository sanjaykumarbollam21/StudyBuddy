# Study Buddy: Bottleneck Analysis & Optimization Hierarchy

## Latency Ranking & Impact Analysis

Based on baseline profiling across client, API, network, database, and inference tiers, the latency bottlenecks in Study Buddy are ranked by their perceived impact on the user experience:

```text
========================================================================================
RANK  SUBSYSTEM                  MEASURED LATENCY   PERCEIVED IMPACT   PRIMARY CAUSE
========================================================================================
1.    Local LLM / Teacher Turn   2,450 - 5,400 ms   CRITICAL           Non-streaming response; waiting for full completion before UI update
2.    Cold App Startup           1,840 - 2,150 ms   HIGH               Eager initialization of AI, voice, & models before rendering shell
3.    Uncached Embeddings        10 - 280 ms        MEDIUM-HIGH        Recalculating identical embeddings on repeated searches & sessions
4.    Planner Multi-Query Load   35 - 72 ms         MEDIUM             Sequential awaits for mastery, revision, exams; unindexed queries
5.    Vector Search at Scale     11 - 118 ms        MEDIUM             Unvectorized Python loop cosine similarity across thousands of chunks
6.    Flutter List Rebuilds      28 ms frame drop   MEDIUM-LOW         Whole-screen setState in Teacher dialogue and Dashboard tabs
7.    Database Unindexed Scans   3 - 36 ms          LOW-MEDIUM         Missing compound indexes on (user_id, topic_id), (user_id, due_date)
========================================================================================
```

---

## Detailed Root Cause Breakdown

### 1. Local LLM Inference (Bottleneck #1 — 2,450 ms - 5,400 ms)
- **Problem**: When a student enters an answer in `InteractiveTeacherScreen` or asks a question via `TutorService.ask_tutor`, the user faces a frozen screen or spinning indicator while the full completion string is generated.
- **Impact**: The UI feels unresponsive for 3 to 5 seconds even on fast hardware.
- **Solution**:
  - Implement token-by-token streaming response.
  - Immediately display "Thinking..." (< 50 ms).
  - Stream tokens progressively as they arrive (first token < 800 ms).
  - Strict context pruning: restrict RAG context from 8,000 characters to `MAX_CONTEXT_TOKENS=1500`, `MAX_RAG_CHUNKS=4`, `MAX_HISTORY_MESSAGES=6`.

### 2. Startup Eager Initialization (Bottleneck #2 — 1,840 ms - 2,150 ms)
- **Problem**: At app launch, heavy subsystems (voice recognition engine, local LLM warm-up, embedding model loading) were triggered before `MainShellScreen` rendered.
- **Impact**: Sluggish cold start perceived by the user on device.
- **Solution**:
  - Render the home shell immediately using cached local session token.
  - Lazily initialize embedding models, local LLM, and voice service upon first user action.

### 3. Uncached Embedding Generation (Bottleneck #3 — 10 ms - 280 ms)
- **Problem**: Identical query texts ("What is a deadlock?", "Explain Banker's algorithm") repeatedly invoked the neural embedding model.
- **Impact**: Redundant CPU cycles, battery drain, and added RAG latency.
- **Solution**:
  - Introduce an in-memory SHA-256 content-hash LRU cache for embeddings.
  - Cache hits return in < 0.01 ms (instantaneous).

### 4. Vector Search & Similarity Matrix (Bottleneck #4 — 11 ms - 118 ms)
- **Problem**: `VectorRepository` performed pure-Python loops computing individual dot products and norms across all user chunks.
- **Impact**: Scales linearly with document size ($O(N)$ Python loop overhead).
- **Solution**:
  - Pre-normalize vectors on ingestion.
  - Use NumPy vectorized matrix multiplication `np.dot(embeddings_matrix, q_vec)` for top-K retrieval.
  - Reduces 10,000-chunk search time from 11.71 ms to 1.38 ms (8.5x speedup).

### 5. Database Query Efficiency (Bottleneck #5 — 3 ms - 36 ms)
- **Problem**: Lack of compound indexes on frequently queried pairs:
  - `(user_id, topic_id)` in `student_mastery`
  - `(user_id, next_review_date)` in `revision_items`
  - `(user_id, status)` in `agent_tasks`
- **Impact**: Table scans when fetching due revisions or mastery.
- **Solution**:
  - Add SQLAlchemy `Index` definitions to `Base.metadata`.
  - Use `asyncio.gather` / `Future.wait` in planner and dashboard data loaders.
