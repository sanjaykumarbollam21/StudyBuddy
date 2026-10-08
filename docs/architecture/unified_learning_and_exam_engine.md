# Study Buddy Unified Architecture: Learning Engine & Exam Intelligence

## 1. Architectural Philosophy

Study Buddy avoids isolating competitive examination tools as disconnected, standalone screens. Instead, the platform is structured around a **Unified Cognitive Architecture** where both academic learning engines and competitive examination engines feed into a single **Mastery Engine**, driving an **Autonomous Study Planner** and **Proactive Agent**.

```
                           STUDY BUDDY
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
          LEARNING ENGINE                 EXAM ENGINE
                 │                             │
          ┌──────┼──────┐               ┌──────┼──────────┐
          │      │      │               │      │          │
       Teacher Practice Revision     Syllabus PYQ     Current Affairs
          │      │      │               │      │          │
          └──────┴──────┴───────────────┴──────┴──────────┘
                                │
                         MASTERY ENGINE
                                │
                         STUDY PLANNER
                                │
                        AUTONOMOUS AGENT
```

```
Exam Profile Definition
       │
       ├── UPSC Civil Services (CSE)
       ├── Staff Selection Commission (SSC CGL)
       ├── Banking (IBPS / SBI PO)
       ├── GATE (Computer Science / Engineering)
       ├── JEE (Main & Advanced)
       ├── NEET (UG Medical)
       ├── State Public Service Commissions (State PSCs)
       ├── UGC NET / JRF
       └── Custom Academic / University Exams
```

---

## 2. Core Subsystems

### A. Learning Engine
* **Teacher Engine**: Socratic multi-turn dialogue, analogy generation, and prerequisite explanation.
* **Practice Engine**: Diagnostic active recall, RAG-grounded application questions, and error analysis.
* **Revision Engine**: SM-2 spaced repetition queue with exponential forgetting curve management.

### B. Exam Engine
* **Syllabus Graph Engine**: Hierarchical DAG (Subject $\to$ Module $\to$ Topic $\to$ Subtopic) with historical exam weight multipliers and topic heatmaps.
* **PYQ Intelligence Engine**: Curated historical questions with strict attribution (`OFFICIAL_COMMISSION_ARCHIVE` vs `PEER_REVIEWED_EXAM_BANK`), marking penalties (-0.33x, -0.83x, -0.25x), and cognitive error classification (`KNOWLEDGE_ERROR`, `READING_ERROR`, `CARELESS_ERROR`, `GUESSING_ERROR`, `TIME_PRESSURE`, `MISCONCEPTION`).
* **Current Affairs & Static Linking Engine**: Strict source verification, publication timestamping, and automatic linkage to constitutional articles and textbook concepts.

### C. Mastery Engine (Central Nervous System)
* Combines telemetry from Socratic lessons, daily active recall ratings, PYQ attempts, and mock tests.
* Maintains dynamic Bayesian mastery estimates ($0.0 - 100.0\%$) per syllabus node.
* Feeds continuous gap telemetry to the Study Planner.

### D. Study Planner Engine
* Dynamic time-blocked scheduling across 4 daily slots:
  1. **Static GS / Core Concepts** (40%)
  2. **Current Affairs & Static Linking** (20%)
  3. **PYQ & Test Series Practice** (25%)
  4. **Answer Writing & Spaced Revision** (15%)
* Powered by the **7-Factor Priority Score Formula**:
  $$\text{Priority Score} = 0.25 G + 0.20 W_{\text{exam}} + 0.20 F_{\text{pyq}} + 0.15 U_{\text{rev}} + 0.10 P_{\text{prox}} + 0.05 R_{\text{weak}} + 0.05 I_{\text{prereq}}$$

### E. Autonomous Agent
* Proactive multi-modal decision engine that routes natural language intents ("What should I study now?", "Quiz me on today's current affairs", "Evaluate my mains answer") to the appropriate engine with explicit safety permission policies.

---

## 3. Data Governance & Integrity Rules

1. **Attribution Demarcation**: Official Commission questions must retain `source_citation="OFFICIAL_COMMISSION_ARCHIVE"` and paper metadata; synthetic questions must be tagged `source_citation="AI_SYNTHESIZED_PRACTICE"`.
2. **Current Affairs Factual Integrity**: The system strictly refuses to hallucinate current events. Every news item requires an authoritative source citation (e.g., *The Hindu*, *PIB*, *RBI Gazette*) and ISO-8601 publication timestamp.
3. **Mains Evaluation Transparency**: All descriptive answer evaluations are clearly presented as **Formative AI Pedagogical Feedback** across 8 defined dimensions, explicitly stating that they are independent of official UPSC government evaluation criteria.

---

## 4. Phase 17 Stress & Scalability Benchmark Results

Empirical results verified on SQLite compound-indexed database with 5,000+ PYQs:
* **Filtered PYQ Query Latency**: **5.51 ms** (Target: $<30$ ms).
* **Current Affairs Static Linking Latency**: **1.36 ms** (Target: $<50$ ms).
* **Mains 8-Rubric Evaluation Calibration**:
  * Incomplete Answer: **3.95 / 10** (39.5%)
  * Exemplary Multi-Dimensional Answer: **7.70 / 10** (77.0%)
* **Backend Automated Test Suite**: **101 / 101 passed (15.76s)**.
* **Flutter Automated Test Suite**: **81 / 81 passed (16.0s)**.
* **Flutter Static Analysis**: **0 issues found**.
