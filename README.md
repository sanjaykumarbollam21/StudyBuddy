# Study Buddy 🎓

> **"Don't just answer the student's question. Teach the student until they understand it."**

Study Buddy is a **Cloud-First AI learning platform** designed for college students, UPSC aspirants, and competitive exam candidates. It pairs enterprise-grade cloud reasoning (Gemini, OpenAI, Claude) with resilient on-device persistence for offline document access, flashcard revision, study planning, and progress tracking.

### 🌐 Cloud-First AI + 📱 Offline Local Persistence
- **Cloud AI (FastAPI Gateway):** Socratic tutoring, UPSC Mains evaluation, current affairs synthesis, dynamic quizzes, and autonomous study agent. Zero provider API keys in client APKs.
- **Offline Persistence (Local SQLite & Cache):** Saved notes, uploaded document text & chunks, spaced repetition flashcard decks, PYQ question bank, and study planner roadmaps remain 100% accessible offline without internet.
- **Honest Connectivity:** No synthetic hallucinations or fake offline models; displays clear connection banners when offline and preserves unsent drafts.

---

## 🏛️ Architecture Overview

The system is built on clean, modular, decoupled architecture:

```
study-buddy/
├── frontend/                # Mobile-first Flutter client (Material 3, Dart)
│   ├── lib/
│   │   ├── core/            # Config, theme, networking, exceptions, constants
│   │   ├── features/        # Auth, Dashboard, Learn, Materials, Practice, Progress, Profile, Tutor
│   │   ├── shared/          # Reusable widgets (AppButton, AppTextField, Badges, ErrorCard)
│   │   └── main.dart        # Entrypoint with auth-guarded routing & theme mode
│   └── test/                # Unit and widget tests
│
├── backend/                 # FastAPI REST & WebSocket backend (Python)
│   ├── app/
│   │   ├── api/             # API v1 routes (/auth, /users, /health)
│   │   ├── core/            # Config (Pydantic BaseSettings), Security (Bcrypt, JWT), DB
│   │   ├── models/          # SQLAlchemy async models (User, Profile, Settings, Notifications)
│   │   ├── schemas/         # Pydantic V2 schemas for validation
│   │   ├── repositories/    # Encapsulated data access layer
│   │   ├── services/        # Business logic services (Auth, Onboarding)
│   │   ├── ai/              # AI provider abstractions (Gemini, OpenAI, Anthropic)
│   │   ├── agents/          # Specialized tutor and research agents
│   │   └── rag/             # Ingestion, chunking, and vector retrieval pipeline
│   ├── tests/               # Pytest async test suite (100% pass)
│   └── main.py              # Application factory with CORS & lifespan
│
├── database/
│   ├── schema.sql           # PostgreSQL normalized schema (24 domain entities + pgvector)
│   └── seed/demo_data.sql   # Demo data for Python, Machine Learning, OS, DBMS
│
├── docs/                    # Architecture diagrams & API reference
├── docker-compose.yml       # Containerized Postgres with pgvector + backend service
└── .env.example             # Documented environment secrets template
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Flutter 3.24+** (with Dart 3.5+)
- **PostgreSQL 16+** with `pgvector` extension (or use built-in SQLite async fallback for instant zero-config testing)

---

### Backend Setup & Execution

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp ../.env.example .env
   ```

4. **Run the Backend Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive OpenAPI documentation is live at: [http://localhost:8000/docs](http://localhost:8000/docs)

5. **Run Backend Tests**:
   ```bash
   python -m pytest tests -v
   ```

---

### Frontend Setup & Execution

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Get dependencies**:
   ```bash
   flutter pub get
   ```

3. **Run Code Analysis**:
   ```bash
   flutter analyze
   ```

4. **Launch Application**:
   - **Chrome Web**:
     ```bash
     flutter run -d chrome
     ```
   - **Windows Desktop**:
     ```bash
     flutter run -d windows
     ```
   - **Android Emulator**:
     ```bash
     flutter run -d emulator-5554
     ```

5. **Run Frontend Tests**:
   ```bash
   flutter test
   ```

---

## 🧪 Quick Test / Demo Student Mode
To test without entering new registration credentials:
1. Launch the Flutter app or Web app.
2. On the Login screen, click **"Quick Start: Demo Student Mode"**.
3. You will immediately access the **Study Buddy Dashboard** with preloaded active courses in Operating Systems, Python, Machine Learning, and DBMS.
4. Tap the floating **"Ask Study Buddy"** button to interact with your AI teacher!

---

## 📋 Development Roadmap

- [x] **Phase 1: Project Foundation, Architecture, Authentication, Database Foundation & UI Shell** *(Complete)*
- [x] **Phase 2: Document Upload, Processing Pipeline & Personal Knowledge Base** *(Complete)*
- [ ] **Phase 3: RAG, Embeddings & Personal Knowledge Search**
- [ ] **Phase 4: AI Teacher Core Engine (Active Teaching Cycle)**
- [ ] **Phase 5: Learning Roadmap Generator**
- [ ] **Phase 6: Quiz Engine & Adaptive Evaluation**
- [ ] **Phase 7: Answer Evaluation & Adaptive Mastery Tracking**
- [ ] **Phase 8: Analytics & Progress Engine**
- [ ] **Phase 9: Study Planner & Spaced Repetition Reminders**
- [ ] **Phase 10: Web Research Mode for New Topics**
- [ ] **Phase 11: Voice Tutor (STT / TTS)**
- [ ] **Phase 12: Exam Mode & Comprehensive Revision System**
