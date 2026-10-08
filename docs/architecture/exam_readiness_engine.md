# Architecture: Exam Readiness & Mock-Test Engine (Phase 7)

## 1. Executive Summary & Purpose
Phase 7 introduces the **Exam Readiness & Mock-Test Engine**, orchestrating Study Buddy's upstream layers:
- **Knowledge Graph & Curriculum** (Phase 4B)
- **AI Teacher / Socratic Learning** (Phase 4A)
- **Practice & Assessment Engine** (Phase 5)
- **Spaced Repetition & SM-2 Scheduling** (Phase 6)

Rather than functioning as a disconnected quiz tool, Phase 7 operationalizes a goal-driven exam preparation system that synthesizes multi-factor readiness diagnostics, enforces realistic blueprint weightings and negative marking, diagnoses cognitive misconceptions, and directly hands off struggling students to the AI Teacher.

```text
                   EXAM GOAL
                      │
             ┌────────▼────────┐
             │ Exam Blueprint  │
             └────────┬────────┘
                      ↓
             Knowledge Graph (Phase 4B)
                      ↓
             Student Mastery (Phase 5)
                      ↓
          Revision / Practice Data (Phase 6)
                      ↓
             ┌───────────────┐
             │ Exam Readiness│
             │    Engine     │
             └───────┬───────┘
                     ↓
              Personalized
                Mock Test
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
   Knowledge      Application    Time Mgmt
    Gaps           Weaknesses     Performance
       │             │             │
       └─────────────┼─────────────┘
                     ↓
               Exam Analysis
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
  Strong Areas               Weak Areas
        ↓                         ↓
    Maintain                 Teacher (Phase 4A) → Practice (Phase 5)
                                  ↓
                             Revision (Phase 6)
```

---

## 2. Core Architectural Components

### A. Exam Blueprint & Topic Weighting
The blueprint defines topic percentages reflecting actual academic syllabus structures:
```text
Operating Systems Exam Blueprint
─────────────────────────────────
Processes                   15%
CPU Scheduling              15%
Synchronization             15%
Deadlocks                   15%
Memory Management           20%
File Systems                10%
I/O Systems                 10%
```

Questions generated for a mock exam proportionally mirror these weights, with varied question types (`mcq`, `multiple_select`, `short_answer`, `scenario`, `coding`), explicit marks per question, and negative marking ratios (default $0.25\times$).

### B. Multi-Factor Exam Readiness Formula
The readiness score is **not** simply an average of quiz percentages. It is a weighted aggregation across 7 cognitive and behavioral dimensions:

$$R = \left( 0.18 \cdot C_{\text{coverage}} + 0.24 \cdot M_{\text{mastery}} + 0.14 \cdot S_{\text{recall}} + 0.14 \cdot P_{\text{practice}} + 0.18 \cdot M_{\text{mock}} + 0.12 \cdot T_{\text{time}} \right) - W_{\text{penalty}}$$

Where:
- $C_{\text{coverage}}$: Fraction of blueprint topics with active learning interaction ($\ge 10\%$ mastery).
- $M_{\text{mastery}}$: Weighted concept mastery across blueprint topics.
- $S_{\text{recall}}$: Active recall retrievability based on SM-2 overdue ratios.
- $P_{\text{practice}}$: Mean accuracy across prior practice drills.
- $M_{\text{mock}}$: Score on simulated mock examinations.
- $T_{\text{time}}$: Time-management index penalizing high ratios of unattempted questions under time constraints.
- $W_{\text{penalty}}$: Severity penalty applied when critical prerequisite topics exhibit deep deficits ($< 40\%$).

Outputs:
1. Quantitative readiness percentage (e.g. `68%`).
2. Qualitative readiness category (`High`, `Moderate`, `At Risk`).
3. Actionable projection:
   > *"At your current study rate, your weakest areas are likely to remain Synchronization and Deadlocks. Spend your next 3 sessions there."*

### C. Real Exam Mode
1. **Live Countdown Timer**: Auto-submits on time expiration.
2. **Question Navigation Palette**:
   - Answered (Emerald)
   - Unanswered (Muted Gray)
   - Marked for Review (Amber with flag)
   - Active Question (Primary Indigo)
3. **Negative Marking Enforcement**:
   - Correct: Full marks awarded.
   - Incorrect: Deducts question negative penalty ($2.5$ marks for $10$-mark question).
   - Unanswered: $0$ marks, $0$ negative deduction.
4. **Interruption Resilience**: Progress state (answers, flags, remaining timer) is cached locally and synchronized with the backend.

### D. Post-Exam Intelligence & Closed-Loop Remediation
Rather than returning a superficial number, Study Buddy delivers:
1. **Overall Score vs Estimated Readiness Comparison**.
2. **Visual Topic Breakdown**: Categorizes each topic into `Strong` ($\ge 80\%$), `Good` ($65-79\%$), `Weak` ($40-64\%$), or `Critical` ($< 40\%$).
3. **Cognitive Diagnostic Synthesis**:
   Detects deep misconceptions from student choices:
   > *"Your biggest problem isn't memorization. Your answers show confusion between deadlock prevention and deadlock avoidance."*
4. **Closed-Loop Socratic Teacher CTA**:
   A single tap on **"Reteach Deadlocks"** immediately launches Phase 4A's `InteractiveTeacherScreen`, generating an adaptive pedagogical dialogue to repair the exact misconception.
