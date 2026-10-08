# Phase 12 Architecture: Advanced Autonomous Study Agent

## 1. System Vision & Overview

Phase 12 transforms Study Buddy from an on-demand AI tutor into an **autonomous proactive learning orchestrator**. Instead of simply waiting for commands like *"What should I study?"*, Study Buddy proactively understands the student's mastery profile, detects unresolved misconceptions, factors in upcoming exam blueprints, and generates explainable, multi-step **Agent Tasks**.

> **"Study Buddy, take care of my preparation for this exam."**

---

## 2. Orchestration Architecture (No Engine Duplication)

The Autonomous Agent functions strictly as an **orchestrator** coordinating existing, battle-tested services rather than duplicating their pedagogical logic:

```text
                     Autonomous Study Agent
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
TeacherEngine            PracticeEngine          RevisionEngine
(Socratic Reteach)      (Targeted Quizzes)       (SM-2 Recall)
       │                       │                       │
       ▼                       ▼                       ▼
MasteryEngine            PlannerEngine           NotificationEngine
(Multi-Factor Calib)    (Timeline Replan)       (Contextual Alerts)
```

---

## 3. Agent Task Domain Model (`AgentTask`)

Every autonomous decision and action is tracked as an explicit, auditable entity:

```text
AgentTask
├── id: UUID
├── goal: "Repair Deadlocks & Synchronization knowledge gap"
├── reason: "Exam is 4 days away. 48% mastery (1.8x weight) with 2 unresolved misconceptions."
├── priority: "critical" | "high" | "medium" | "low"
├── permission_level: "recommend" | "requires_permission" | "autonomous"
├── current_state: "proposed" | "approved" | "executing" | "completed" | "rejected"
├── allocated_minutes: 60
├── proposed_actions: [
│   ├── Step 1: TeacherEngine (Socratic Reteaching, 25m)
│   ├── Step 2: PracticeEngine (Diagnostic Quiz, 20m)
│   ├── Step 3: RevisionEngine (Active Recall, 15m)
│   └── Step 4: MasteryEngine (Calibrate Mastery & Replan, 0m)
│ ]
├── execution_result: {"summary": "...", "mastery_delta": +15.5%}
└── explanation_breakdown: {"top_topic": "Deadlocks", "score": 92.4, ...}
```

---

## 4. Multi-Factor Decision Engine (`AgentDecisionEngine`)

The decision engine continuously evaluates:

$$\text{TaskPriorityScore} = (\text{MasteryGap} \times 40) + (\text{ExamWeight} \times \text{ExamUrgency} \times 25) + (\text{MisconceptionPenalty} \times 20) + (\text{RevisionUrgency} \times 15)$$

### Time Allocation Algorithm
* **60+ Minutes**: 25 min Socratic remediation + 20 min targeted practice + 15 min active recall revision + mastery calibration.
* **30–45 Minutes**: 18 min conceptual breakdown + 12 min targeted practice + mastery calibration.
* **15 Minutes (Micro-Session)**: Rapid active recall queue review.

---

## 5. Safety Boundary & Permission Levels

Autonomous actions are strictly constrained by the `ActionPermissionPolicy`:

| Permission Level | Permitted Actions | Description |
|---|---|---|
| **Level 1: Recommend** | Study session suggestions, alternative topics | Soft suggestions displayed to the student |
| **Level 2: Requires Permission** | Multi-step remediation sessions, changing exam dates, altering study schedule | Prompts student: *"[Start Autonomous Session] [Not now]"* |
| **Level 3: Autonomous (Safe)** | Background plan recalculation, quiz preparation, SM-2 interval updates, notifications | Executed automatically without blocking the student |

---

## 6. Transparent Explainability Framework

Every decision made by the agent can be inspected on demand:

> **Student:** *"Why did you choose this?"*  
> **Agent:** *"I prioritized Deadlocks & Synchronization because:  
> 1. Your current mastery is only 48%, which is well below your target of 80%.  
> 2. It carries a heavy weight (1.8x) on your upcoming exam in 4 days.  
> 3. Recent attempts revealed repeated misconceptions between prevention and avoidance.  
> 4. You have 3 revision items due that should be reinforced to prevent forgetting.  
> This plan yields the highest score improvement per study minute."*

---

## 7. Verification Summary

```text
Backend Test Suite (pytest):
  tests/test_auth.py                     PASSED
  tests/test_documents.py                PASSED
  tests/test_rag.py                      PASSED
  tests/test_semantic_quality.py         PASSED
  tests/test_teaching_engine.py          PASSED
  tests/test_curriculum_graph.py         PASSED
  tests/test_practice_engine.py          PASSED
  tests/test_revision_engine.py          PASSED
  tests/test_exam_engine.py              PASSED
  tests/test_voice_multimodal.py         PASSED
  tests/test_study_planner.py            PASSED
  tests/test_production_sync.py          PASSED
  tests/test_e2e_validation_hardening.py PASSED
  tests/test_autonomous_agent.py         PASSED
  ------------------------------------------------
  Total: 72/72 PASSED (100%)

Flutter Test Suite (flutter test):
  test/widget_test.dart                  PASSED
  test/document_management_test.dart     PASSED
  test/rag_search_tutor_test.dart        PASSED
  test/teaching_engine_test.dart         PASSED
  test/roadmap_test.dart                 PASSED
  test/practice_test.dart                PASSED
  test/revision_test.dart                PASSED
  test/exam_test.dart                    PASSED
  test/voice_multimodal_test.dart        PASSED
  test/planner_test.dart                 PASSED
  test/production_sync_test.dart         PASSED
  test/e2e_golden_journey_test.dart      PASSED
  test/autonomous_agent_test.dart        PASSED
  ------------------------------------------------
  Total: 59/59 PASSED (100%)

Flutter Static Analysis:
  flutter analyze: 0 issues found!
```
