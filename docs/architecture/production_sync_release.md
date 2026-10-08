# Phase 10 & 10.5 Architecture: Production, Persistence, Sync & Release

## 1. System Overview

Phase 10 turns Study Buddy into a production-grade, highly dependable application designed for daily student use. It provides:
1. **Offline-First Synchronization Engine (`SyncEngine` & `SyncService`)**: Seamless operation with zero internet, local change tracking, timestamped watermarks, and deterministic conflict resolution upon reconnection.
2. **Production Security & Hardening**: Path traversal prevention, safe filename sanitization, upload size/MIME filtering, and in-memory rate limiting.
3. **Proactive Study Notifications**: Contextual learning nudges (Study Session Kickoff, Due Spaced Revision Items, Exam Proximity Alerts).
4. **Real AI Provider Configuration**: User-configurable operation modes (🟢 Offline AI, 🟡 Hybrid AI, 🔵 Online AI).
5. **Phase 10.5: Learning Intelligence Hardening**: Multi-factor mastery calculation and dynamic topic urgency scoring.
6. **Continuous Integration & Release Pipeline**: Automated GitHub Actions CI workflow executing backend pytest, Flutter static analysis, and widget tests.

```text
               Study Buddy Architecture
                         │
          ┌──────────────┴──────────────┐
          │                             │
    LOCAL CLIENT                   SERVER / CLOUD
  (Flutter SQLite/Prefs)       (PostgreSQL / FastAPI)
          │                             │
          └──────────────┬──────────────┘
                         │
              Offline-First Sync Engine
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
    Upload Changes               Download Changes
   (Mastery, Plans,             (Server Changelogs &
    Revision Progress)           Sync Watermarks)
          │                             │
          └────── Conflict Resolution ──┘
              (Deterministic Merging)
```

---

## 2. Synchronization Architecture

### 2.1 Changelog & Watermarks
- **`SyncChange` Entity**: Tracks entity mutations (`mastery`, `revision_item`, `study_plan_item`), action types, timestamps, and json payloads.
- **`DeviceSyncState`**: Tracks the last synchronized timestamp watermark per registered device.
- **Deterministic Merge Strategy**:
  - `StudentMastery`: Combines highest practice counts, applies the latest timestamp evaluation, and merges weak topic areas.
  - `RevisionItem`: Retains the latest SM-2 repetition interval, ease factor, and mastery score.
  - `StudyPlanItem`: Records completed statuses and scores without overriding future scheduled milestones.

---

## 3. Phase 10.5 Learning Intelligence Hardening

### 3.1 Multi-Factor Mastery Equation
Traditional simplistic moving averages are upgraded to a pedagogical formulation:

$$\text{Mastery} = f(\text{Recent Acc}, \text{Hist Acc}, \text{Difficulty}, \text{Question Type}, \text{Mistakes}, \text{Misconceptions}, \text{Recall Interval}, \text{Prerequisites}, \text{Confidence})$$

- **Difficulty Weighting**: Questions categorized by cognitive load (0.5 easy to 1.5 hard).
- **Question Complexity**: `recall` (0.8x), `conceptual` (1.0x), `applied` (1.15x), `coding` (1.25x).
- **Ebbinghaus Forgetting Curve Decay**: Retention decay based on days elapsed since previous recall scaled by memory stability.
- **Prerequisite Gating**: Topics are capped at 75% mastery if prerequisite competencies fall below 50%.

### 3.2 Dynamic Topic Urgency Scoring
```python
urgency = (
    (mastery_gap * 40.0)
    + (exam_weight * exam_factor * 15.0)
    + (revision_urgency * 20.0)
) * prereq_mult * speed_adjustment
```

---

## 4. Proactive Study Notifications

Three categories of proactive alerts keep students on track:
1. **Session Kickoff**: *"Your 30-minute study session is starting. Ready to continue Deadlocks?"*
2. **Revision Due**: *"You have 4 revision items due today in Operating Systems."*
3. **Exam Countdown & Mastery Warning**: *"Your OS exam is 5 days away. Synchronization is still below your target mastery."*

---

## 5. Security Hardening

- **Filename Sanitization**: Rejects paths with `..`, slashes, and control characters to prevent directory traversal.
- **Upload Validation**: Restricts uploads strictly to `.pdf`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg` under 25MB.
- **Rate Limiting**: Sliding-window rate limiter protecting sensitive API routes.

---

## 6. Verification & Test Metrics

- **Backend Pytest**: 60/60 tests passing (`test_production_sync.py`, `test_study_planner.py`, `test_voice_multimodal.py`, etc.).
- **Flutter Analyzer**: 0 issues (`flutter analyze`).
- **Flutter Test Suite**: 53/53 tests passing across all components, sync services, and UI flows.
- **CI/CD**: Configured via `.github/workflows/ci.yml`.
