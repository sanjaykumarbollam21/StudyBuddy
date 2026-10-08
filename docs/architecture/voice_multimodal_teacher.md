# Phase 8: Voice & Multimodal Teacher Architecture

## 1. Executive Summary & Design Vision

Phase 8 elevates Study Buddy from a text-based learning platform to an **embodied, conversational AI tutor sitting right beside the student**. 

Rather than deploying an isolated, separate "chatbot", Phase 8 provides a **unified multimodal voice layer** directly on top of the established learning loop (RAG, Socratic Teacher, Curriculum DAG, Practice Engine, Spaced Repetition, and Exam Readiness).

```text
                           ┌─────────────────────────┐
                           │         Student         │
                           └────────────┬────────────┘
                                        │
                         Voice Audio / Text / Visuals
                                        │
                                        ▼
                 ┌─────────────────────────────────────────┐
                 │       Multimodal Teacher Interface      │
                 │   - Animated Pulsing Visualizer HUD     │
                 │   - Interruptible Speech Synthesis (TTS)│
                 │   - Real-Time STT Transcription         │
                 │   - Attached Visuals Tray & Grounding   │
                 └──────────────────────┬──────────────────┘
                                        │
                         Conversation Turn / Payload
                                        │
                                        ▼
                 ┌─────────────────────────────────────────┐
                 │    Conversation Context Manager         │
                 │   - Voice Intent Classification         │
                 │   - Socratic State Sync                 │
                 │   - Mastery & Weak Area Injection       │
                 │   - Document Page Context Anchoring     │
                 └──────────────────────┬──────────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                ▼                       ▼                       ▼
      ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
      │   RAG Engine     │    │  Teacher Engine  │    │ Curriculum Graph │
      │  Hybrid Search   │    │ Socratic Pedagogy│    │ Prerequisite DAG │
      └─────────┬────────┘    └─────────┬────────┘    └─────────┬────────┘
                │                       │                       │
                └───────────────────────┼───────────────────────┘
                                        ▼
                           ┌─────────────────────────┐
                           │ Practice & Mastery Hub  │
                           └────────────┬────────────┘
                                        ▼
                           ┌─────────────────────────┐
                           │ Revision & Exam Engines │
                           └─────────────────────────┘
```

---

## 2. Voice Dialogue & Conversation Manager

### 2.1 Natural Intent Classification

Student spoken speech is parsed via the `ConversationContextManager` ([backend/app/voice/context_manager.py](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/backend/app/voice/context_manager.py)) into discrete pedagogical intents:

1. **`explain_topic`**: Student asks for a conceptual overview ("Explain deadlocks to me").
2. **`quiz_me`**: Student initiates an active recall challenge ("Quiz me on this concept").
3. **`hint`**: Student asks for scaffolding without receiving the direct answer ("Give me a hint").
4. **`simplify`**: Student is confused; triggers real-world metaphors or simplified models ("Make it easier", "I don't understand").
5. **`next_question`**: Advances the pedagogical state machine to the subsequent concept or step.
6. **`page_explanation`**: Anchors spoken explanation to a specific page or paragraph ("Explain page 42").
7. **`image_explanation`**: Deconstructs diagrams, charts, handwritten notes, or code screenshots.
8. **`answer`**: Evaluates the student's spoken answer against Socratic criteria.

### 2.2 Socratic Speech Script Synthesis

Text formatted with complex markdown, asterisks, tables, or emojis sounds unnatural when fed to TTS engines. The `VoiceService._clean_for_speech()` function normalizes teaching responses into smooth conversational prose:
- Strips markdown headers (`###`, `**`)
- Expands acronyms and bullet points into natural spoken transitions
- Converts code notation into spoken terminology
- Emphasizes conversational rhythm and pauses

---

## 3. Multimodal Visual Analysis Engine

The `MultimodalService` ([backend/app/multimodal/service.py](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/backend/app/multimodal/service.py)) supports 5 primary categories of student study material:

| Visual Category | Detection Heuristic | Pedagogical Synthesis Output |
|---|---|---|
| **Architectural Diagrams** | Directed graphs, flowchart blocks, wait-for cycles | Cycle breakdown, state transitions, deadlock Coffman conditions |
| **Mathematical Formulas** | LaTeX, sigma summations, probabilities | Derivation walk-through, variable definitions, intuition |
| **Code Snippets** | Syntactic structures, semaphores, loops | Step-by-step trace, concurrency pitfalls, execution flow |
| **Handwritten Notes** | Organic text, margin annotations, bullet points | Core takeaway synthesis, error checking, summary |
| **Textbook Pages** | Column layout, figure captions, exercise boxes | Page-anchored teaching, key paragraph decoding, Socratic check |

### 3.1 Grounded Visual Walkthrough

Each multimodal response yields:
1. `title`: Human-readable identifier.
2. `visual_elements`: Structured list of detected visual nodes, arrows, or code lines.
3. `conceptual_explanation`: Deep pedagogical breakdown with RAG citations.
4. `spoken_script`: Conversational audio script tailored for listening.
5. `check_question`: Immediate Socratic question to verify comprehension.
6. `suggested_voice_prompts`: Contextual follow-up chips.

---

## 4. Offline-First Architecture & Resilient Fallbacks

Consistent with Study Buddy's architectural mandate:
- **No Mandatory Cloud API Key**: If external vision or cloud speech services are offline, local intelligence rules immediately synthesize accurate fallback explanations, diagrams, and quizzes.
- **Interruptible Speech**: The student can interrupt the teacher at any moment via the audio HUD or by speaking, causing an immediate audio stop and transitioning to listening mode.
- **Dual Input Modes**: Seamless toggle between Spoken Voice and Text Keyboard fallback with visual media attachment.

---

## 5. Verification & Test Suite

### Backend Test Coverage (51 / 51 Passed)
- `tests/test_voice_multimodal.py`: Intent classification, Wait-For-Graph diagram deconstruction, CPU Gantt/paging analysis, speech script sanitization, document page grounding, and voice turn integration.
- Regression tests across Auth, RAG, Hybrid Search, Curriculum Graph, Practice Engine, Spaced Repetition, and Mock Exams all remain 100% green.

### Frontend Test Coverage (39 / 39 Passed)
- `test/voice_multimodal_test.dart`:
  - `MultimodalAnalysisModel` & `VoiceTurnModel` JSON serialization.
  - `VoiceApiService` offline fallback synthesis for diagrams, page 42 grounding, hints, analogies, and quizzes.
  - `VoiceTeacherScreen` HUD rendering with animated visualizer orb, greeting dialogue, quick prompt chips, multimodal attachments, and teacher speech interruption.
- 0 lint errors, 0 analyzer issues (`flutter analyze` clean).
