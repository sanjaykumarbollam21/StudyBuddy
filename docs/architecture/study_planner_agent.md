# Phase 9: Intelligent Study Planner & AI Study Agent Architecture

## 1. Executive Summary & Core Purpose

Phase 9 transforms Study Buddy from an on-demand AI Teacher into a **proactive, autonomous AI study companion**. 

Rather than generating a static, rigid calendar that fails when life happens, Study Buddy **continuously re-plans** the student's learning journey based on:
1. Target exam deadlines
2. Daily study time availability
3. Curriculum prerequisite DAGs
4. Real-time mastery gaps and weak areas
5. Spaced repetition (SM-2) review queues
6. Mock exam cognitive diagnostics

```text
                    STUDENT GOAL
                         │
          ┌──────────────┴──────────────┐
          │                             │
       Exam Date                  Available Time
          │                             │
          └──────────────┬──────────────┘
                         ▼
                STUDY PLANNER AGENT
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
   Curriculum         Mastery          Revision
   Dependencies       Weak Areas       Due Items
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                 PRIORITY ENGINE
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Today's Plan          Long-term Plan
              │                     │
              ▼                     ▼
        Learn / Practice       Revision / Mock
              │                     │
              └──────────┬──────────┘
                         ▼
                   STUDENT ACTION
                         │
                         ▼
                 RESULTS / MASTERY
                         │
                         └──────→ REPLAN
```

---

## 2. Dynamic Re-Planning Engine (`StudyPlannerEngine`)

### 2.1 Multi-Phase Trajectory Synthesis
When a plan is generated (e.g. *12 days, 2 hours/day = 24.0 hours*), the engine computes an optimal 4-phase trajectory:

| Phase | Days Range | Primary Focus | Pedagogical Mechanism |
|---|---|---|---|
| **Phase 1: Gap Closing & Core Remediation** | Days 1–4 (~35%) | High-yield weak areas (*Deadlocks*, *Synchronization*) | Socratic Concept Teaching (`InteractiveTeacherScreen`) + immediate comprehension checks |
| **Phase 2: Interleaved Retrieval Practice** | Days 5–8 (~35%) | Problem-solving under mixed conditions | 20-question practice drills (`InteractiveQuizScreen`) + daily SM-2 active recall queues |
| **Phase 3: Simulated Mock Exam Runs** | Days 9–10 (~15%) | Cognitive stamina & time management | Full timed mock exam with negative marking (`MockExamScreen`) |
| **Phase 4: Targeted Weakness Repair & Polish** | Days 11–12 (~15%) | Post-mock error resolution & formula polish | High-priority rapid remediation on identified mock mistakes |

### 2.2 Graceful Absorption of Missed Sessions
When a student says *"I missed yesterday's study session"* or misses two days:
- The system **never** marks the timetable as "failed" or punishes the student.
- Past unfinished items are marked as `skipped` with clear audit notes.
- The engine recalculates remaining days and available hours:
  - Compresses secondary review.
  - Strictly protects high-yield weak area remediation and final mock exams.
  - Generates clear pedagogical rationale explaining how the schedule adapted.

### 2.3 Micro-Session Optimizer
When a student has limited available time:
- **<= 20 Minutes**: Launches high-frequency **Active Recall** retrieval queue on overdue items.
- **25–40 Minutes**: Launches a 15-question **Targeted Practice Quiz** on the student's #1 weak topic with instant Socratic feedback.
- **>= 45 Minutes**: Launches a **Socratic Concept Deep Dive** with the AI Teacher beside them.

---

## 3. Conversational Agent Task Layer (`StudyAgentService`)

The Agent Task Layer allows the student to converse naturally with their study companion, which routes directly to underlying engines:

| Student Intent | Example Utterance | Agent Behavior & Routed Action |
|---|---|---|
| `plan_preparation` | *"I have my OS exam in 12 days and can study 2 hours every day."* | Synthesizes 4-phase plan; presents immediate Day 1 action. |
| `what_next` | *"What should I study now?"* | Analyzes Day N queue; recommends highest-priority pending task. |
| `micro_session` | *"I have 30 minutes right now."* | Configures 15-question drill on lowest-mastery topic. |
| `handle_missed_day` | *"I missed yesterday's study session."* | Recalculates remaining trajectory without penalties. |
| `reschedule_exam` | *"Move my exam to next Monday."* | Updates target deadline; adjusts daily workload density. |
| `focus_weak_areas` | *"Focus more on the topics I'm weak at."* | Elevates lowest-mastery topics (< 65%) to top of schedule. |
| `execute_action` | *"Give me today's lesson."* | Launches Socratic Teacher (`socratic_lesson`). |
| `execute_action` | *"Start my revision."* | Launches Spaced Repetition queue (`active_recall`). |
| `execute_action` | *"Start a 20-question practice session."* | Launches Practice Quiz engine (`practice_quiz`). |
| `execute_action` | *"Test whether I'm ready for the exam."* | Launches Full Mock Exam session (`mock_exam`). |

---

## 4. Database Models & Schema Design

### `StudyPlan` ([backend/app/models/planner.py](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/backend/app/models/planner.py))
- `id` (UUID): Unique identifier.
- `user_id` (ForeignKey): User isolation.
- `title` (str): e.g., *"Operating Systems Exam Mastery Preparation Plan"*.
- `subject` (str): Target subject.
- `exam_date` (DateTime): Target exam deadline.
- `daily_study_minutes` (int): Target daily study allocation (default 120 mins).
- `total_days` (int): Total duration in days.
- `total_available_hours` (float): Dynamic total available hours.
- `current_day` (int): Current day in the active plan (1..N).
- `status` (str): `active`, `completed`, `paused`, `archived`.
- `strategy_summary` (JSON): 4-phase descriptions, high-yield topic list, and re-planning rationale.
- `last_replanned_at` (DateTime): Audit timestamp of last recalculation.

### `StudyPlanItem` ([backend/app/models/planner.py](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/backend/app/models/planner.py))
- `id` (UUID): Unique session item identifier.
- `plan_id` (ForeignKey): Parent plan.
- `day_number` (int): Scheduled day number.
- `session_type` (str): `learn`, `practice`, `revision`, `mock_exam`, `weak_repair`.
- `topic` (str): Targeted topic or concept.
- `allocated_minutes` (int): Duration in minutes.
- `priority_weight` (float): Urgency weight (0.0 to 1.0).
- `status` (str): `pending`, `in_progress`, `completed`, `skipped`.
- `action_type` (str): `socratic_lesson`, `active_recall`, `practice_quiz`, `mock_exam`.
- `action_payload` (JSON): Parameters required to launch the exact engine.
- `performance_score` (float): Recorded score after session completion.

---

## 5. Verification & Quality Assurance

### Backend Pytest Suite
- **55 / 55 tests passed** (`tests/test_study_planner.py` + full regression suite).
- Verified: Multi-phase plan synthesis, dynamic re-planning on missed days, 15/30/60 minute micro-session optimization, and agent conversational task routing.

### Frontend Flutter Suite
- **48 / 48 tests passed** (`test/planner_test.dart` + all Phase 1–8 test suites).
- Verified: Data model serialization, API service offline fallbacks, Planner HUD rendering, quick prompt chips, action execution, and dynamic re-plan modal bottom sheet.
- **`flutter analyze`**: **0 issues found** across the entire codebase.
