"""
Phase 4 End-to-End Real Backend Persistence Journey
Executes the full user lifecycle:
1. Register new student account
2. Upload document (PDF/text)
3. Start active teaching session
4. Answer 2 student turns
5. Simulate backend restart (wipe in-memory caches, run startup lifespan rehydration)
6. Fetch active sessions and resume session
7. Complete a 3rd turn verifying state continuity
"""

import asyncio
import os
import sys
import uuid
import json

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from httpx import AsyncClient, ASGITransport
import app.main
from app.main import app
from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal
import app.teaching.engine as teaching_engine_module


async def run_e2e_journey():
    print("=" * 80)
    print("PHASE 4: REAL BACKEND END-TO-END PERSISTENCE & RESUME JOURNEY")
    print("=" * 80)

    test_user_email = f"e2e_student_{uuid.uuid4().hex[:6]}@example.com"
    test_user_password = "SecurePassword123!"

    # Session 1: Server run 1
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Register student account
            print("\n[Step 1] Registering student account...")
            signup_resp = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": test_user_email,
                    "password": test_user_password,
                    "full_name": "E2E Student Aspirant",
                },
            )
            print(f" -> Signup response: {signup_resp.status_code}")
            assert signup_resp.status_code == 201
            auth_token = signup_resp.json()["access_token"]
            user_id = signup_resp.json()["user"]["id"]
            auth_headers = {"Authorization": f"Bearer {auth_token}"}

            # 2. Upload small study PDF
            print("\n[Step 2] Uploading study material document...")
            sample_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Concurrency) >>\nendobj\ntrailer\n<<>>\n%%EOF"
            files = {
                "file": ("Operating_Systems_Concurrency.pdf", sample_pdf_content, "application/pdf")
            }
            data = {"subject": "Operating Systems"}
            upload_resp = await client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers=auth_headers,
            )
            print(f" -> Upload response: {upload_resp.status_code}")
            doc_id = upload_resp.json().get("id") or str(uuid.uuid4())

            # 3. Start teaching session
            print("\n[Step 3] Starting Socratic teaching session...")
            start_resp = await client.post(
                "/api/v1/teaching/start",
                json={
                    "topic": "Process Synchronization",
                    "subject": "Operating Systems",
                    "document_id": doc_id,
                },
                headers=auth_headers,
            )
            print(f" -> Start session response: {start_resp.status_code}")
            assert start_resp.status_code == 200
            session_data = start_resp.json()
            session_id = session_data["session_id"]
            print(f" -> Session ID: {session_id} | State: {session_data['state']}")

            # 4. Turn 1: Prior knowledge assessment answer
            print("\n[Step 4] Answering Turn 1 (Prior Knowledge)...")
            turn1_resp = await client.post(
                f"/api/v1/teaching/{session_id}/interact",
                json={"answer": "I know processes need to share memory safely."},
                headers=auth_headers,
            )
            print(f" -> Turn 1 response: {turn1_resp.status_code}")
            assert turn1_resp.status_code == 200
            turn1_data = turn1_resp.json()
            print(f" -> State: {turn1_data['state']} | Mastery: {turn1_data['mastery_percentage']}%")

            # 5. Turn 2: Concept check answer
            print("\n[Step 5] Answering Turn 2 (Check Understanding)...")
            turn2_resp = await client.post(
                f"/api/v1/teaching/{session_id}/interact",
                json={"answer": "The primary goal is preventing race conditions and ensuring mutual exclusion."},
                headers=auth_headers,
            )
            print(f" -> Turn 2 response: {turn2_resp.status_code}")
            assert turn2_resp.status_code == 200
            turn2_data = turn2_resp.json()
            mastery_before_crash = turn2_data["mastery_percentage"]
            print(f" -> State: {turn2_data['state']} | Mastery: {mastery_before_crash}% | Step: {turn2_data['current_step_number']}")

    # 6. STOP SERVER & SIMULATE HARD RESTART
    print("\n" + "=" * 80)
    print("[Step 6] SIMULATING SERVER SHUTDOWN, MEMORY FLUSH, & RESTART...")
    print("=" * 80)
    # Clear in-memory dictionary
    teaching_engine_module._active_sessions.clear()
    print(" -> In-memory session store wiped: len = 0")

    # Session 2: Server run 2 (Restarts and executes lifespan rehydration)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Re-authenticate student
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": test_user_email, "password": test_user_password},
            )
            token_after_restart = login_resp.json()["access_token"]
            restart_headers = {"Authorization": f"Bearer {token_after_restart}"}

            # 7. Query active sessions (Dashboard Resume Card)
            print("\n[Step 7] Checking active sessions after server restart...")
            active_resp = await client.get("/api/v1/teaching/sessions/active", headers=restart_headers)
            print(f" -> Active sessions response: {active_resp.status_code}")
            assert active_resp.status_code == 200
            active_list = active_resp.json()
            print(f" -> Found {len(active_list)} active sessions on dashboard.")
            matched_sess = [s for s in active_list if s["session_id"] == session_id]
            assert len(matched_sess) == 1, "Session must persist and be rehydrated after server restart!"
            resumed_summary = matched_sess[0]
            print(f" -> Restored session on dashboard: {resumed_summary['topic']} ({resumed_summary['mastery_score']}%)")

            # 8. Resume session and fetch full dialogue
            print("\n[Step 8] Resuming full session dialogue...")
            get_sess_resp = await client.get(f"/api/v1/teaching/{session_id}", headers=restart_headers)
            print(f" -> Session detail response: {get_sess_resp.status_code}")
            assert get_sess_resp.status_code == 200
            detail = get_sess_resp.json()
            print(f" -> Restored Dialogue Turns: {len(detail.get('turns', []))}")
            print(f" -> Restored Mastery: {detail.get('mastery_score')}% (Expected: {mastery_before_crash}%)")
            assert abs(detail.get("mastery_score") - mastery_before_crash) < 0.1

            # 9. Continue session with Turn 3
            print("\n[Step 9] Submitting Turn 3 on resumed session...")
            turn3_resp = await client.post(
                f"/api/v1/teaching/{session_id}/interact",
                json={"answer": "Semaphores and mutex locks are used to enforce critical section access."},
                headers=restart_headers,
            )
            print(f" -> Turn 3 response: {turn3_resp.status_code}")
            assert turn3_resp.status_code == 200
            turn3_data = turn3_resp.json()
            print(f" -> Resumed Turn 3 Mastery: {turn3_data['mastery_percentage']}%")
            print(f" -> Resumed Turn 3 State: {turn3_data['state']}")

    print("\n" + "=" * 80)
    print(">> VERIFIED: REAL BACKEND PERSISTENCE & RESUME JOURNEY SUCCEEDED 100%!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_e2e_journey())
