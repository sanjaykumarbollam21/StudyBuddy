# Study Buddy — Cloud-First AI Migration & Offline AI Removal Audit
**Document ID**: `SB-ARCH-MIGRATION-AUDIT-001`  
**Date**: October 8, 2026  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  

---

## 1. Executive Summary

Study Buddy is transitioning from a hybrid/on-device pseudo-offline AI architecture to a **production-grade, Cloud-First AI learning architecture**. 

### Strategic Distinction
- **Offline AI Inference Engine**: **REMOVED**. On-device LLM generation, model file packaging, warm-singleton lifecycle states, and local fabricated responses are deprecated and eliminated.
- **Offline Access to Learning Data & Utilities**: **PRESERVED & HARDENED**. User documents, extracted text & chunks, cached PYQs, syllabus taxonomy, spaced repetition schedules, study planner calendar, student mastery maps, and scheduled reminders remain fully functional offline without requiring an LLM.
- **AI Tutoring, Evaluation & Agent**: **ONLINE CLOUD AI**. High-fidelity reasoning, Socratic dialogue, Mains formative feedback, current affairs synthesis, and autonomous planning run exclusively via the FastAPI cloud gateway using secure cloud LLMs (Gemini / OpenAI / Anthropic) with server-side secrets.

---

## 2. Inventory of Components

### 2.1 Backend AI Components (`backend/app/`)

| Component / File | Current Role | Migration Action | Rationale |
| :--- | :--- | :--- | :--- |
| `app/core/config.py` | Defines `AI_MODE="offline"`, `OFFLINE_ONLY=False`, API keys. | **Modify**: Set `AI_MODE="cloud"`, add `AI_TIMEOUT_SECONDS`, `AI_MAX_RETRIES`, `GEMINI_MODEL`, `OPENAI_MODEL`. | Enables cloud-first routing by default and removes offline AI execution locks. |
| `app/tutor/providers/base.py` | Abstract `LLMProvider` interface. | **Modify**: Add asynchronous streaming method `stream_response(...)`, request metadata, timeout context. | Standardizes streaming and cancellation across cloud models. |
| `app/tutor/providers/gemini.py` | Google Gemini API provider. Currently blocked if `AI_MODE=="offline"`. | **Modify**: Remove offline exception. Add exponential backoff retries, error mapping, and streaming support. | Primary high-performance cloud reasoning engine. |
| `app/tutor/providers/openai.py` | OpenAI GPT-4o / GPT-4o-mini provider. | **Modify**: Remove offline exception, add structured outputs and streaming. | Secondary/fallback cloud reasoning engine. |
| `app/tutor/providers/mock.py` | Deterministic mock LLM for testing. | **Retain**: Keep for fast, deterministic, zero-cost unit and integration testing. | Essential for continuous integration without external API dependencies. |
| `app/tutor/providers/local.py` | Simulated local heuristic Socratic engine. | **Deprecate / Remove from Production**: Keep only as fallback during test execution if no API key is present. | Eliminate pre-saved/canned text generation. |
| `app/tutor/providers/llama_cpp.py` / `ollama.py` | Local daemon clients. | **Deprecate / Decouple**: Not deployed in cloud production. | Simplifies maintenance. |
| `app/tutor/providers/__init__.py` | Provider factory `get_llm_provider()`. | **Modify**: Default to `gemini` (or `openai`), then `mock` in test mode. Never return canned strings in production. | Clean cloud provider resolution. |
| `app/teaching/engine.py` | Pedagogical Socratic state machine. | **Retain & Enhance**: Driven by cloud LLM provider and authenticated database sessions. | Core pedagogical differentiator. |
| `app/teaching/curriculum.py` | Lesson step generation. | **Retain**: Dynamically grounds steps in RAG chunks or cloud LLM. | Ensures uploaded materials are taught authentically. |
| `app/search/hybrid.py` | Vector search & BM25 hybrid search. | **Retain**: Independent of LLM inference; indexes and retrieves document chunks. | Essential for grounded RAG context. |
| `app/embeddings/` | Semantic embedding providers. | **Retain**: Local or cloud embeddings remain active for document chunk search. | Needed for document grounding. |

---

### 2.2 Frontend Mobile Components (`frontend/lib/`)

| Component / File | Current Role | Migration Action | Rationale |
| :--- | :--- | :--- | :--- |
| `core/storage/android_local_llm_provider.dart` | Singleton on-device LLM engine with `ModelLifecycleState` and token streaming simulation. | **Deprecate / Refactor**: Remove on-device inference state machine and fake generation. Replace with a thin `CloudAIStatusService` or decouple. | Eliminates misleading local LLM claims and memory bloat. |
| `features/settings/screens/diagnostics_screen.dart` | Runs local LLM inference benchmarks and tests on-device latency. | **Modify**: Update diagnostics to test **Cloud API Connectivity & Latency** instead of on-device LLM inference. | Accurately reflects cloud-first production architecture. |
| `features/teaching/services/teaching_api_service.dart` | Calls `/teaching` API, with hardcoded offline fallback turn generation. | **Modify**: When offline or backend is unreachable, throw typed `NetworkConnectionException` and display non-blocking retry banner. Never fabricate turns. | Honesty in UX; no canned deadlock responses. |
| `features/dashboard/screens/tutor_sheet.dart` | AI Tutor drawer; had offline response simulation. | **Modify**: Display clear "Connection Required: Connect to the internet to consult Study Buddy Cloud AI" when offline. Keep document preview visible. | Clean separation of online AI vs offline content. |
| `features/voice/services/voice_api_service.dart` | Multimodal and voice teacher service. | **Modify**: Require cloud connectivity for speech-to-text AI reasoning; gracefully notify user when offline. | Voice reasoning requires cloud models. |
| `features/exam/services/exam_api_service.dart` | Mains evaluation and exam questions. | **Modify**: Mains evaluation requires cloud AI; PYQ search and questions remain cached locally in `OfflineStorageService`. | UPSC Mains evaluation requires deep LLM rubric scoring. |
| `core/storage/offline_storage_service.dart` | Local SharedPreferences/cache for documents, chunks, revision, mastery, schedule. | **PRESERVE & HARDEN**: Keep 100% of local storage for notes, chunks, progress, and user isolation. | User data remains safely accessible offline. |
| `features/documents/` & `materials_tab.dart` | Document extraction, chunking, reading, and storage. | **PRESERVE**: Users can view, search, and manage notes offline. | Document viewer must always work offline. |
| `features/revision/` | Spaced repetition algorithm (SM-2/FSRS). | **PRESERVE**: Deterministic flashcard scheduling works completely offline. | Spaced repetition does not need an LLM. |
| `features/planner/` | Study planner calendar and time tracking. | **PRESERVE**: Schedule storage and tracking work completely offline. | Planning calendar is local-first. |

---

## 3. Current vs. Proposed Architecture

### Current Architecture (Hybrid / Flawed Fallback)
```
[User Request] 
      │
      ▼
[Is Connected?] ──No──► [Local Fake Fallback / AndroidLocalLLMProvider]
      │                      │
      │ Yes                  └──► Canned "Deadlocks" / "Page 12" text
      ▼
[FastAPI Backend]
      │
      ▼
[Settings.AI_MODE == 'offline'?] ──Yes──► [LocalLLMProvider Heuristic]
      │
      │ No
      ▼
[Cloud LLM (Gemini / OpenAI)]
```

### Proposed Cloud-First Architecture
```
┌────────────────────────────────────────────────────────────────────────┐
│                        STUDY BUDDY FLUTTER APP                         │
├───────────────────────────────────┬────────────────────────────────────┤
│         ONLINE AI FEATURES        │        OFFLINE LOCAL ENGINE        │
│  • Socratic AI Teacher & Dialogue │  • Saved Notes & Chunk Browser     │
│  • UPSC Mains 250w Evaluation     │  • Spaced Repetition Flashcards    │
│  • Current Affairs Synthesis      │  • PYQ Question Bank & Filters     │
│  • Autonomous Study Agent         │  • Study Planner & Pomodoro Timer  │
│  • Dynamic Adaptive Quizzes       │  • Mastery Map & Progress History  │
└─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                  │                                    │
           HTTPS (Secure API)                 Local SQLite / Prefs
                  │                                    │
                  ▼                                    ▼
┌───────────────────────────────────┐        [Offline Storage Service]
│          FASTAPI BACKEND          │        (Full isolated user cache)
├───────────────────────────────────┤
│  • Auth & User Isolation          │
│  • Cloud Provider Gateway         │
│    (Gemini 1.5 Flash / Pro,       │
│     OpenAI GPT-4o-mini / GPT-4o)  │
│  • Streaming & Retry Resilience   │
│  • Server-Side Secrets & RAG      │
└─────────────────┬─────────────────┘
                  │
                  ▼
┌───────────────────────────────────┐
│          CLOUD AI ENGINES         │
│  • Google Gemini Cloud API        │
│  • OpenAI Cloud API               │
└───────────────────────────────────┘
```

---

## 4. Connectivity & Graceful Degradation Strategy

| User State | Action in AI Teacher / Tutor | Action in Materials / Notes | Action in Revision / Planner |
| :--- | :--- | :--- | :--- |
| **Online (Normal)** | Live streaming AI dialogue, instant evaluation, source citations. | Full reading, chunking, and cloud synchronization. | Full sync with cloud mastery state. |
| **Offline / Unreachable** | Shows non-blocking banner: *"Internet connection required for AI Teacher. Connect to Wi-Fi/Mobile data to resume tutoring."* Input is preserved. | 100% accessible. Student can read, search, and review all saved materials. | 100% accessible. Spaced revision reviews can be completed and queued for sync. |

---

## 5. Security & Privacy Guarantees
1. **Zero Provider Secrets on Client**: `GEMINI_API_KEY` and `OPENAI_API_KEY` exist **only** in backend environment variables (`.env`). No API keys are bundled into Flutter assets or Android release APKs.
2. **Context Minimization**: When asking questions about documents, the backend sends **only the relevant RAG chunks** (top-3/4 snippets), never the entire 50MB document, minimizing token costs and protecting privacy.
3. **User Isolation**: Every document chunk and chat session is strictly scoped to `user_id` verified by JWT token.

---

## 6. Implementation Action Plan

1. **Phase 2 (Cloud AI Backend)**: Update `backend/app/core/config.py`, `backend/app/tutor/providers/` to streamline cloud model execution with bounded retries, streaming, and error handling.
2. **Phase 3 (Deprecate Local AI)**: Update `diagnostics_screen.dart`, remove obsolete on-device model simulation from frontend, update settings.
3. **Phase 4 (Connectivity UI)**: Add friendly `ConnectionBanner` / offline state handling to `InteractiveTeacherScreen`, `TutorSheet`, and `VoiceTeacherScreen`.
4. **Phase 5-8 (Verification & Tests)**: Update test suites, run `pytest`, `flutter analyze` (0 errors), `flutter test`, and build Android APK.
5. **Phase 9 (Final Report)**: Deliver comprehensive documentation in `docs/architecture/cloud_first_migration_report.md`.
