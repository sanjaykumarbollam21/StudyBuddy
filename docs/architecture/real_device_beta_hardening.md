# Phase 15 — Real Device Beta & Release Hardening

## Overview

Phase 15 transitions Study Buddy from feature development into **Real Device Beta & Release Hardening**. This phase specifically validates physical Android device reliability, offline runtime autonomy, diagnostic observability, and resilience against real-world mobile operating system conditions (process death, battery saving, thermal throttling, network toggles, and reboot events).

---

## 1. Architecture: True Separation of Runtimes

Study Buddy enforces a strict runtime boundary between Desktop development/testing daemons, Android on-device inference, and optional cloud fallbacks:

```text
                           LLMProvider Interface
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
   Desktop Local AI          Android On-Device AI       Cloud AI (Optional)
          │                          │                          │
  ┌───────┴───────┐           ┌──────┴──────┐            ┌──────┴──────┐
  │ Ollama Server │           │ Mobile GGUF │            │  Gemini Pro │
  │ (Port 11434)  │           │ Or Mobile   │            │  OpenAI API │
  ├───────────────┤           │ Runtime Lib │            └─────────────┘
  │ llama.cpp     │           ├─────────────┤
  │ (Port 8080)   │           │ 100% Offline│
  └───────────────┘           │ Zero Desktop│
                              │ Dependency  │
                              └─────────────┘
```

### Runtime Profiles

1. **Desktop Host (Dev / CI / Regression)**:
   - Windows 11 / Linux / macOS.
   - Dual engine support: `OllamaLLMProvider` (`/api/generate`) and `LlamaCppLLMProvider` (native server `/completion` & `/v1/chat/completions`).
   - 16 GB RAM safeguards: context window capped (`n_predict: 512`, `temperature: 0.3`, batch processing limits).

2. **Android Physical Device (Release / Beta)**:
   - `AndroidLocalLLMProvider` operates natively inside the mobile sandbox.
   - No loopback / Wi-Fi bridge to a PC server.
   - Socratic dialog generation with built-in heuristic/template safety fallbacks when device RAM is constrained.
   - Native embeddings via on-device BGE-small / MiniLM models.

3. **Cloud Providers (Optional Fallback)**:
   - Activated only when user requests cloud inference and internet connectivity is verified.

---

## 2. Study Buddy Diagnostics Screen

To diagnose real-device beta issues, the app includes a telemetry dashboard accessible from the Profile tab (`DiagnosticsScreen`).

### Telemetry Cards Monitored

| Section | Monitored Metrics |
|---|---|
| **AI Mode** | Offline mode status, fallback policy, active provider |
| **LLM Engine** | Android Local Model name, quant type, context window, latency |
| **Embeddings** | BGE-small (384-dimensional), normalization, local vector index status |
| **Vector Search** | In-memory & SQLite vector table health, cosine similarity engine |
| **Local Database** | Documents count, chunks count, active transactions, cache integrity |
| **Autonomous Agent**| Active tasks, paused tasks, crashed task recovery status |
| **Sync Engine** | Pending mutations, conflict resolution policy, last sync timestamp |
| **Notifications** | OS permission status, scheduled alarm count (study kickoff, revision, exam countdown) |
| **Memory & Battery**| Model memory footprint, app memory usage, background scheduler status |

### Interactive Diagnostic Self-Test
The screen provides an on-device self-test button that exercises:
1. Local LLM response ping.
2. Embedding vector computation.
3. Database query latency.
4. Notification alarm manager scheduling.

---

## 3. Real-Device Offline Verification (25-Step Test)

The system is validated against the complete end-to-end student journey in 100% offline mode:

```text
 1. Install APK on physical Android device
 2. Create local student profile
 3. Import textbook document (PDF / Markdown / Text)
 4. Disable device Internet (Airplane mode / Wi-Fi & Cellular OFF)
 5. Generate learning path from knowledge graph
 6. Start interactive Socratic lesson
 7. Ask teacher a question
 8. Provide an intentionally incorrect answer
 9. Trigger misconception detection and pedagogical remediation
10. Launch targeted practice session
11. Verify mastery progression (BKT / ELO updates)
12. Verify revision scheduled via SM-2 algorithm
13. Request proactive study agent guidance
14. Terminate/close app (simulated OS kill)
15. Reopen app
16. Resume interrupted AgentTask safely
17. Lock device screen
18. Unlock device screen
19. Reboot device (simulated RECEIVE_BOOT_COMPLETED)
20. Verify rescheduled notification triggers
21. Re-enable Internet connectivity
22. Trigger delta-sync with remote server
23. Verify zero duplicate entities generated
24. Complete simulated mock exam
25. Verify exam readiness score update
```

Automated verification tests are codified in:
- Backend: [test_android_production_runtime.py](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/backend/tests/test_android_production_runtime.py)
- Frontend: [android_production_runtime_test.dart](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/frontend/test/android_production_runtime_test.dart)
- Frontend: [real_device_beta_test.dart](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/frontend/test/real_device_beta_test.dart)

---

## 4. Android Manifest & Permissions

Configured in `frontend/android/app/src/main/AndroidManifest.xml`:
- `android.permission.INTERNET`: For cloud sync when enabled.
- `android.permission.POST_NOTIFICATIONS`: Android 13+ (API 33) proactive study alerts.
- `android.permission.RECEIVE_BOOT_COMPLETED`: Restores alarm schedules after phone reboot.
- `android.permission.VIBRATE`: Tactile feedback for study timers and exam reminders.
- `android.permission.WAKE_LOCK`: Ensures critical agent tasks and background sync finish execution during sleep states.

---

## 5. Background Lifecycle & Crash Recovery

1. **Process Death / Interrupted Tasks**:
   - The backend and frontend orchestrators monitor task status.
   - Any task left in `executing` state upon process restart is automatically transitioned to `paused` with preserved execution history (`recover_interrupted_tasks`).
   - Resuming executes the next pending step idempotently without re-running completed steps.

2. **Alarm Manager Persistence**:
   - `NotificationService.handleDeviceReboot()` re-hydrates scheduled alarms from `OfflineStorageService` whenever `RECEIVE_BOOT_COMPLETED` is received.
