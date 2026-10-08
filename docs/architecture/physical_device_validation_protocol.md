# Phase 16: Physical Device Validation & Release Candidate Protocol

## Overview

Automated test suites (81/81 Pytest + 67/67 Flutter) prove architectural consistency, mathematical correctness, and state resilience under simulated conditions. However, **real Android hardware introduces non-simulated variables**:
- OS process killing under memory pressure (low-RAM OOM killer)
- Thermal throttling after extended local token generation
- Manufacturer-specific battery saver restrictions (Doze mode, Xiaomi/Samsung background killers)
- Real storage latency and physical screen lock cycles

**Phase 16 serves as the definitive manual validation gatekeeper** before releasing Study Buddy as a production Release Candidate (RC).

---

## 1. Release Build & APK Installation

### Prerequisites
- Android device running Android 9.0+ (API level 28 or higher, recommended API 33+ for notification permissions).
- USB debugging enabled on the physical phone.
- Android SDK platform-tools installed with `adb`.

### Build Commands
```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Clean and fetch fresh dependencies
flutter clean
flutter pub get

# 3. Build optimized Release APK (ARM64 / ARMv7)
flutter build apk --release --split-per-abi

# Or build single universal release APK
flutter build apk --release

# 4. Install onto connected physical phone via ADB
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

---

## 2. The 25-Step Real-Device Offline Journey

Execute this exact sequence on your physical device using a real textbook (e.g., an Operating Systems or Computer Architecture PDF/EPUB/Markdown):

| Step | Action on Physical Phone | Expected Hardware / UI Outcome | Verification Check |
|:---|:---|:---|:---:|
| **1** | Install and launch release APK on phone | Splash screen displays; opens to Auth or Main Shell. | [ ] |
| **2** | Create a local student profile | Local profile persists in SQLite; no network calls made. | [ ] |
| **3** | Import real textbook file (PDF or TXT) | Document parsed into semantic chunks; chunk count displayed in Diagnostics. | [ ] |
| **4** | **Enable Airplane Mode** (Turn Wi-Fi & Cellular OFF) | Device status shows offline; app continues without popup errors. | [ ] |
| **5** | Generate a learning path / roadmap | Curriculum knowledge graph generates modules and milestones on-device. | [ ] |
| **6** | Launch an interactive Socratic lesson | Local Socratic engine presents initial probe without lag or spinner hang. | [ ] |
| **7** | Ask the AI Teacher a conceptual question | Contextually grounded answer generated utilizing textbook chunks. | [ ] |
| **8** | Provide an intentionally incorrect answer | Teacher evaluates response as incorrect; does not hallucinate praise. | [ ] |
| **9** | Trigger misconception handling | System identifies specific root misconception and explains the underlying principle. | [ ] |
| **10** | Launch targeted practice session | Retrieval questions tailored to the misconception appear. | [ ] |
| **11** | Verify mastery changes | Mastery score updates dynamically (e.g., 65% → 85%) on the dashboard. | [ ] |
| **12** | Verify revision is scheduled | Active recall flashcard added to Spaced Repetition queue with SM-2 interval. | [ ] |
| **13** | Ask Study Agent what to study next | Multi-step autonomous `AgentTask` proposed with clear rationale. | [ ] |
| **14** | **Force-close the app** (Swipe away from Android Recents) | App process terminates while `AgentTask` is executing. | [ ] |
| **15** | Relaunch Study Buddy | Crash recovery silently detects interrupted task and transitions it to `paused`. | [ ] |
| **16** | Resume `AgentTask` | Task resumes from the exact interrupted action step without re-running earlier steps. | [ ] |
| **17** | **Lock the phone screen** (Screen OFF) | Device enters screen-off sleep; no crashes or memory spikes. | [ ] |
| **18** | Unlock the phone screen | Study Buddy resumes seamlessly with zero layout flicker or lost state. | [ ] |
| **19** | **Reboot the physical phone** | Phone shuts down and restarts cleanly. | [ ] |
| **20** | Check notification schedule after reboot | `RECEIVE_BOOT_COMPLETED` re-primes alarms; study notifications trigger on time. | [ ] |
| **21** | **Disable Airplane Mode** (Turn Wi-Fi / Cellular ON) | Connectivity restored; `SyncService` detects active network. | [ ] |
| **22** | Trigger sync | Local mutations stream to remote backend without blocking UI thread. | [ ] |
| **23** | Verify zero duplicate records | Textbooks, mastery scores, and revision cards remain 1-to-1 without duplication. | [ ] |
| **24** | Run a simulated Mock Exam | 5–10 timed exam questions administered across covered topics. | [ ] |
| **25** | Inspect Exam Readiness Score | Exam Readiness metric recalculates and reflects cumulative mastery. | [ ] |

---

## 3. The Uncomfortable Real-World Edge Cases

After completing the 25-step golden journey, stress-test the following mobile environmental conditions:

```text
 1. Low Battery (<15%)        → Verify Android battery saver doesn't abort background task saves.
 2. Low Storage (<300 MB)      → Verify graceful storage warnings rather than silent corruption.
 3. Airplane Mode Toggling    → Flip airplane mode ON and OFF rapidly during an active lesson.
 4. Flaky 2G / 3G Simulation  → Verify app prioritizes local LLM over failing remote endpoints.
 5. OOM Killer Stress         → Open 5 heavy games/apps to force Android to evict Study Buddy.
 6. Extended Backgrounding    → Leave phone idle overnight (8 hrs); verify wake lock alarms fire.
 7. Heavy Document (300+ pgs) → Import large textbook; verify chunking doesn't freeze the UI.
 8. Long Lesson (30+ turns)   → Verify memory doesn't leak or throttle after extended conversation.
 9. Rapid Button Tapping      → Double-tap submit/next rapidly; verify no double-mutations occur.
10. Dynamic AI Mode Switch    → Toggle Offline → Cloud → Hybrid in Settings without restarting.
```

---

## 4. Hardware Telemetry & Metrics Log

Record the observed physical metrics during testing:

| Metric | Target Threshold | Physical Measured Value | Pass / Fail |
|:---|:---:|:---:|:---:|
| **App RAM (Idle)** | < 120 MB | ________ MB | [ ] |
| **App RAM (During Lesson)** | < 250 MB | ________ MB | [ ] |
| **On-Device LLM Memory** | < 1.2 GB (GGUF Q4) | ________ MB | [ ] |
| **First Token Latency (Local)** | < 1.5 seconds | ________ s | [ ] |
| **Generation Speed** | > 8 tokens/sec | ________ tps | [ ] |
| **Battery Drain (30m study)** | < 6% battery drop | ________ % | [ ] |
| **Device Temperature** | Normal / Warm (No Thermal Throttling) | ________ °C | [ ] |
| **Cold Startup Time** | < 1.8 seconds | ________ s | [ ] |

---

## 5. In-App Release Check Verification

The in-app diagnostics dashboard (`Profile` → `Study Buddy Diagnostics`) exposes the **Release Check & Validation** card:

1. **Automated Verification**: Displays `✓ 81 Pytest + 67 Flutter PASSED`.
2. **Physical Device Validation**: Initially displays `⚠ Physical device test pending (Manual 25-step protocol)`.
3. Once the 25 physical steps and edge cases above are completed successfully on your phone:
   - Tap **Mark Passed** directly on the phone in `DiagnosticsScreen`.
   - The status updates and permanently persists locally as:
   ```text
   RELEASE CHECK & VALIDATION
   ✓ Automated Verification: 81 Pytest + 67 Flutter PASSED
   ✓ Physical Device Validation: 25-step physical journey verified on hardware
   ```
