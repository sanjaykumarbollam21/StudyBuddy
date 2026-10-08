# Study Buddy — Phase 21: Real-Device Beta Validation Protocol

**Target Milestone:** Release Candidate 1 (RC-1)  
**Target Hardware:** Realme Physical Device (`ca87b7ae`), Android 13/14  
**Release Artifacts:**
- Universal Release APK: `build/app/outputs/flutter-apk/app-release.apk` (**53.21 MB**)
- Target ARM64 Release APK: `build/app/outputs/flutter-apk/app-arm64-v8a-release.apk` (**18.64 MB**)

---

## 1. Environment Architecture & URL Validation (Implemented in RC-1)

To prevent arbitrary endpoints from acting as unverified authentication destinations, the mobile app now enforces explicit environment separation in [login_screen.dart](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/frontend/lib/features/auth/screens/login_screen.dart) and [app_config.dart](file:///c:/Users/sanja/OneDrive/Desktop/Study%20Buddy/frontend/lib/core/config/app_config.dart):

```
┌─────────────────────────────────────────────────────────────┐
│                 SERVER ENVIRONMENT PRESETS                  │
├─────────────────────────────────────────────────────────────┤
│ • Production (Default): https://api.studybuddy.app/api/v1   │
│   (Enforces trusted TLS; zero local fallback)               │
│                                                             │
│ • Local LAN Wi-Fi:      http://192.168.88.16:8000/api/v1    │
│   (Allowed for private subnet validation without USB)       │
│                                                             │
│ • Custom: Validated URI scheme (http/https), host check,    │
│   and warning badges for non-HTTPS public endpoints         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Four Core Physical Device Beta Tests

### Test 1 — Standalone Launch & PC Independence
* **Pre-condition:** Release APK installed on the Realme phone.
* **Procedure:**
  1. Unplug the USB cable from the PC.
  2. Kill any ADB reverse port forwarding commands (`adb reverse --remove-all`).
  3. Ensure the phone is connected only to Wi-Fi or mobile data.
  4. Launch **Study Buddy** from the Android home screen / app drawer.
  5. Tap the **Server Connection** icon (`Icons.dns_rounded`) on the login screen to verify the target endpoint.
  6. Sign in with student credentials or tap **Quick Start: Demo Student Mode**.
* **Pass Criteria:**
  - App cold starts within **< 1.0 second**.
  - Dashboard loads cleanly without PC tethering.
  - No connection timeout or crash on startup.

---

### Test 2 — Complete Document-Grounded Learning Session
* **Pre-condition:** App launched and authenticated on the Realme device.
* **Procedure:**
  1. Navigate to **Materials** tab and upload an authentic textbook excerpt (e.g., *Modern Indian History* or *Operating Systems*).
  2. Tap **"Teach me from this document"** to launch `InteractiveTeacherScreen`.
  3. Verify the AI Teacher introduces the lesson using the document's actual title and section content.
  4. Deliberately submit an incorrect answer to the first check question.
  5. Verify that the Socratic remediation loop triggers with an intuitive analogy.
  6. Submit the correct answer and advance to Step 2.
  7. Complete a practice question and review the **Spaced Repetition** flashcard deck.
* **Pass Criteria:**
  - Zero canned fallback text (no unprompted "Deadlocks" if History was uploaded).
  - Accurate page/section citation displayed in the header.
  - Mastery score increments and persists in local SQLite upon completion.

---

### Test 3 — Disconnect, Draft Preservation & Network Recovery
* **Pre-condition:** Inside an active Socratic lesson on the phone.
* **Procedure:**
  1. Begin typing an answer in the response input field (e.g., *"The movement paused because of violence at Chauri Chaura"*).
  2. Turn on **Airplane Mode** (disable Wi-Fi and mobile data).
  3. Tap **Submit**.
  4. Observe the UI response.
  5. Turn **Airplane Mode OFF** (restore internet).
  6. Tap **Retry**.
* **Pass Criteria:**
  - **No freeze or ANR:** The app displays an honest, non-blocking connection banner.
  - **Zero draft loss:** The student's typed text remains intact in the input field.
  - **Clean recovery:** Upon reconnecting, the turn submits cleanly without duplicate messages.

---

### Test 4 — Multi-Account Isolation & Non-Leakage
* **Pre-condition:** Student A has uploaded private notes and created study milestones.
* **Procedure:**
  1. Sign out of Student A's account via **Profile > Log Out**.
  2. Create a new account for Student B (`student_beta_002@example.com`).
  3. Navigate to **Materials** tab.
  4. Navigate to **Spaced Repetition / Flashcards**.
  5. Check active study plans and revision history.
* **Pass Criteria:**
  - Student A's documents are **completely invisible** to Student B.
  - Flashcard decks, mastery history, and progress snapshots are fresh and empty for Student B.
  - Direct retrieval of Student A's document IDs returns `403 Forbidden` or `Not Found`.

---

## 3. Physical Device Telemetry Thresholds

During a 30-minute test cycle on the Realme hardware:
- **RAM Footprint:** Maximum 220 MB (compared to 2+ GB in the deprecated on-device LLM build).
- **Battery Consumption:** < 4% total drain over 30 minutes of mixed active tutoring.
- **Thermal Behavior:** No perceptible temperature rise (< 36°C battery temperature).
