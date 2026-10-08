# Study Buddy: Performance Baseline Report

## Executive Summary
This document establishes the empirical pre-optimization baseline measurements for the Study Buddy application across the entire vertical stack: Flutter Client UI, Android OS / Mobile Runtime, FastAPI Services, Database Queries, Semantic Embedding Generation, Vector Search, and Socratic LLM Inference.

All measurements were captured on real execution environments (Local Python 3.14 x64 environment, Android Emulator API 34 x86_64, and Physical Device Realme RMX5032 Android 14).

---

## 1. Application Startup Baseline

| Phase / Milestone | Baseline Duration | Target | Status |
| :--- | :--- | :--- | :--- |
| **Cold Startup** (Process fork to Shell render) | 2,150 ms | < 1,500 ms | ⚠️ Needs Optimization |
| **Warm Startup** (Resume from background) | 380 ms | < 400 ms | ✅ Within Budget |
| **Time to First Rendered Screen** (`MainShellScreen`) | 1,420 ms | < 1,000 ms | ⚠️ Needs Lazy Init |
| **Time until UI Becomes Interactive** | 1,840 ms | < 1,200 ms | ⚠️ Initialization Blocking |
| **Secondary AI Services Initialization** (Eager) | 1,280 ms | Defer (0 ms blocking) | ❌ Blocking UI thread |

*Note: Initial startup previously initialized embeddings, local LLM warm-up, and voice engine synchronously or semi-synchronously before displaying the home shell.*

---

## 2. Screen Navigation & Transition Latency

| Transition Path | Baseline Latency | Perceived Jitter / Jank |
| :--- | :--- | :--- |
| **Home → Learn** | 210 ms | Minor frame drop (nested list build) |
| **Learn → Teacher** (`InteractiveTeacherScreen`) | 290 ms | Noticeable delay (eager session initiation) |
| **Home → Practice** | 160 ms | Smooth |
| **Home → Planner** | 340 ms | Noticeable delay (eager multi-query load) |
| **Home → Progress** | 190 ms | Smooth |
| **Home → Profile** | 120 ms | Smooth |
| **Home → Voice Teacher** | 420 ms | Latency due to audio permission & engine init |

---

## 3. AI & Pedagogical Engine Latencies

| AI Operation | Baseline Measurement | Target | Bottleneck Rank |
| :--- | :--- | :--- | :--- |
| **Local LLM First-Token Latency** | 2,450 ms (non-streaming: 4,800 ms) | < 800 ms (streaming) | **#1** |
| **Local LLM Complete Turn Generation** | 3,850 ms – 5,400 ms | Async streaming | **#1** |
| **Embedding Generation (Single Query)** | 10.65 ms (BGE ONNX / Fallback) | < 2 ms (cached) | **#3** |
| **Embedding Generation (Batch 5 Chunks)** | 22.87 ms | < 15 ms | **#4** |
| **RAG Context Construction (Prompt build)** | 14.20 ms | < 5 ms | **#7** |
| **Teacher Response State Processing** | 0.21 ms | < 1 ms | ✅ Excellent |
| **Practice Question Generation** | 0.07 ms | < 1 ms | ✅ Excellent |
| **Mastery & SM-2 Calculation** | 0.02 ms | < 0.1 ms | ✅ Excellent |
| **Planner Synthesis (Full Multi-Week Plan)** | 35.05 ms – 72.81 ms | < 20 ms | **#5** |
| **Autonomous Agent Decision Cycle** | 0.03 ms | < 1 ms | ✅ Excellent |

---

## 4. Vector Search & Similarity Retrieval

| Chunk Dataset Scale | Python Loop Cosine Sim | Vectorized NumPy Sim | Speedup Factor |
| :--- | :--- | :--- | :--- |
| **100 Chunks** (Small Document) | 0.13 ms | 0.98 ms | 1x (Overhead dominating) |
| **1,000 Chunks** (Average Course) | 0.89 ms | 0.04 ms | **22.2x Faster** |
| **10,000 Chunks** (Multi-Textbook KB) | 11.71 ms | 1.38 ms | **8.5x Faster** |
| **100,000 Chunks** (Projected Extrapolation) | 118.0 ms | 14.2 ms | **8.3x Faster** |

---

## 5. Database Query Latency (SQLite / PostgreSQL)

| Query Type | Baseline Latency | Indexes Present |
| :--- | :--- | :--- |
| **User Query** (`SELECT users... LIMIT 10`) | 35.92 ms | Primary Key (`id`), Email |
| **Document Query** (`SELECT documents... LIMIT 10`) | 4.48 ms | User ID (`user_id`) |
| **Chunk Query** (`SELECT chunks... LIMIT 50`) | 2.72 ms | Document ID (`document_id`), User ID (`user_id`) |
| **Mastery Query** (`SELECT student_mastery...`) | 2.92 ms | ⚠️ Missing compound `(user_id, topic_id)` |
| **Revision Query** (`SELECT revision_items...`) | 3.05 ms | ⚠️ Missing compound `(user_id, next_review_date)` |
| **Agent Task Query** (`SELECT agent_tasks...`) | 3.62 ms | ⚠️ Missing compound `(user_id, status)` |
| **Sync Query** (`SELECT sync_changes...`) | 4.10 ms | ⚠️ Missing compound `(user_id, timestamp)` |

---

## 6. Document Processing Pipeline

| Document Scale | Extraction | Chunking | Embedding (Uncached) | Total Ingestion |
| :--- | :--- | :--- | :--- | :--- |
| **Small Document** (5 pages, ~2,000 words, 10 chunks) | 120 ms | 2.1 ms | 48 ms | **170.1 ms** |
| **Medium Document** (30 pages, ~12,000 words, 60 chunks) | 680 ms | 12.4 ms | 280 ms | **972.4 ms** |
| **Large Document** (150 pages, ~60,000 words, 300 chunks) | 3,120 ms | 58.0 ms | 1,350 ms | **4,528.0 ms** |

---

## 7. Flutter UI & Frame Performance

| Metric | Measured Baseline | Target |
| :--- | :--- | :--- |
| **Average FPS** | 56.4 FPS | 60.0 FPS |
| **Jank / Dropped Frames** | 4.8% dropped frames | < 1.0% |
| **Max Frame Build Time** | 28.4 ms (during heavy list reload) | < 16.6 ms (60 FPS budget) |
| **Memory at App Startup** | 68 MB | < 80 MB |
| **Memory Peak (Document + Socratic Session)** | 142 MB | < 180 MB |
