# Study Buddy System Architecture

## Overview
Study Buddy is built as an AI-powered personal learning platform that functions as an attentive personal teacher.

```
+-----------------------------------------------------------+
|                    Flutter Frontend                       |
| (Mobile-first, Material 3, Clean Architecture, GoRouter) |
+-----------------------------+-----------------------------+
                              | HTTPS / WSS
+-----------------------------v-----------------------------+
|                      FastAPI Backend                      |
|       - Modular Routers (/auth, /users, /documents, etc.) |
|       - Security (Bcrypt, JWT Tokens)                     |
|       - Core Services & Repository Pattern                |
+--------------+-----------------------------+--------------+
               |                             |
+--------------v-------------+ +-------------v--------------+
|    Relational Database     | |    AI & RAG Engine         |
| PostgreSQL + pgvector      | | Multi-provider abstraction |
| (SQLite dev fallback)      | | (Gemini, OpenAI, Anthropic)|
+----------------------------+ +----------------------------+
```

## Layer Separation
- **Presentation Layer**: Flutter client (Mobile/Web/Desktop)
- **API Layer**: FastAPI endpoints with request validation using Pydantic V2
- **Service Layer**: Business logic, auth verification, learning progression
- **Repository Layer**: Encapsulated database operations with SQLAlchemy AsyncSession
- **Data Layer**: Normalized relational schema with pgvector vector embeddings

## Database Architecture
Normalized PostgreSQL schema encompassing 24 domain entities:
1. `users`: Credentials, active status, verification
2. `profiles`: Education level, target goals, learning style, daily study budget
3. `user_settings`: Audio speed, theme, notifications, provider selection
4. `subjects`: User subjects (e.g. Operating Systems, ML, DBMS, Python)
5. `collections`: Nested organization for personal knowledge base
6. `documents`: Ingested files, status tracking, page counts, metadata
7. `document_chunks`: Text chunks with pgvector embeddings
8. `topics` & `topic_relations`: Knowledge graph relationships (prerequisites, dependencies)
9. `learning_paths` & `learning_path_topics`: Generated sequential roadmaps
10. `lessons` & `lesson_progress`: Interactive lessons and comprehension markers
11. `quiz_sessions`, `questions`, `answers`: Quiz generation & deep answer evaluation
12. `student_mastery`: Concept-level mastery tracking and weak-spot detection
13. `study_plans` & `study_sessions`: Spaced schedules and historical logs
14. `revision_items`: SM-2 spaced repetition engine
15. `exam_sessions`: Full exam simulation with detailed diagnostic reporting
16. `research_sources`: Citable authoritative references
17. `chat_sessions` & `chat_messages`: Conversational tutor with sources and action chips
18. `notifications`: Study reminders, revision alerts, and milestone updates

## Document Pipeline & Knowledge Base (Phase 2)
- Ingestion of PDF, DOCX, TXT, and Markdown files with 50 MB limit and path traversal security.
- Modular extractors (`PDFExtractor`, `DOCXExtractor`, `TXTExtractor`, `MarkdownExtractor`).
- Text cleaning (Unicode NFKC, whitespace, line-wrap fixes) and hierarchical section detection.
- Semantic chunking with sentence-boundary preservation and metadata tagging.
- State machine transitions (`UPLOADING` -> `UPLOADED` -> `PROCESSING` -> `EXTRACTING` -> `CLEANING` -> `CHUNKING` -> `INDEXING` -> `READY` / `FAILED`).
- Multi-tenant isolation ensuring strict privacy and access control.
- Detailed documentation available at [docs/architecture/document_pipeline.md](document_pipeline.md).

## RAG & Retrieval Engine (Phase 3)
- **Offline-First & Provider-Independent Architecture**: Complete operation possible without internet connectivity or external API keys using deterministic local embeddings (`LocalEmbeddingProvider`) and local tutoring.
- **Dynamic Vector Dimensions**: Vector dimensions are provider-determined (e.g. 384 for local, 768 for Gemini, 1536 for OpenAI) and never hardcoded.
- **Hybrid Retrieval Engine**: Combines dense semantic vector similarity with lexical keyword matching, technical term boosting, and query normalization.
- **Anti-Hallucination Guardrails & Grounding Modes**: Supports `strict_materials`, `materials_plus_general`, and `general` tutoring with similarity thresholding.
- **Authentic Citations**: Responses include verifiable citations with document names, page numbers, section headers, and snippets.
- **Detailed Documentation**: Available at [docs/architecture/rag_architecture.md](rag_architecture.md) and [docs/architecture/embedding_pipeline.md](embedding_pipeline.md).

## AI Teacher Engine (Phase 4A)
- **Active Socratic Teaching Loop**: Moves beyond passive RAG chat into a multi-turn pedagogical state machine (`Assess` -> `Teach One Concept` -> `Check Understanding` -> `Evaluate` -> `Remediate` -> `Re-test` -> `Advance`).
- **Concept Breakdown**: Deconstructs study topics into bite-sized, sequential sub-concepts with physical analogies and check questions.
- **First-Class LLM Provider Abstraction**: Supports `LocalLLMProvider` (100% offline, zero network requests, semantic answer matching via `bge-small-en-v1.5`), `CloudLLMProvider` (Gemini, OpenAI with strict pedagogical instructions), and `MockLLMProvider`.
- **Diagnostic Answer Evaluation**: Identifies exact misconceptions (e.g. CPU speed vs. resource deadlock) and awards mastery points.
- **Adaptive Remediation Engine**: Re-explains with simpler analogies and guided Socratic hints when students struggle.
- **Interactive Flutter Teaching Workspace**: Structured concept cards, analogy callouts, check questions, evaluation banners, and progress tracking.
- **Detailed Documentation**: Available at [docs/architecture/teaching_engine.md](teaching_engine.md).
