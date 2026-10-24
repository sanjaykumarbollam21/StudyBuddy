"""
Study Buddy Endpoint Smoke Testing Script
Runs HTTP requests across all API routes with a test account,
verifying that every route responds cleanly without unhandled 5xx errors.
"""

import asyncio
import os
import sys
import uuid
from typing import Dict, Any, List

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


async def run_endpoint_smoke_tests():
    print("=" * 80)
    print("STUDY BUDDY API ENDPOINT SMOKE TEST SUITE")
    print(f"Target: FastAPI Application ({settings.PROJECT_NAME} v{settings.VERSION})")
    print("=" * 80)

    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 1: Smoke test public routes
            health_resp = await client.get("/health")
            print(f"[HEALTH] GET /health -> {health_resp.status_code}")
            assert health_resp.status_code == 200

            root_resp = await client.get("/")
            print(f"[ROOT] GET / -> {root_resp.status_code}")
            assert root_resp.status_code == 200

            # Step 2: Create a test user account
            test_email = f"qa_smoke_{uuid.uuid4().hex[:8]}@example.com"
            test_password = "SecurePassword123!"
            signup_payload = {
                "email": test_email,
                "password": test_password,
                "full_name": "QA Smoke Engineer",
            }
            signup_resp = await client.post("/api/v1/auth/signup", json=signup_payload)
            print(f"[AUTH] POST /api/v1/auth/signup -> {signup_resp.status_code}")
            assert signup_resp.status_code == 201

            # Login to obtain JWT
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": test_email, "password": test_password},
            )
            print(f"[AUTH] POST /api/v1/auth/login -> {login_resp.status_code}")
            assert login_resp.status_code == 200
            token = login_resp.json().get("access_token")
            assert token is not None and len(token) > 10
            auth_headers = {"Authorization": f"Bearer {token}"}

            # Step 3: Enumerate OpenAPI endpoints
            openapi = app.openapi()
            paths = openapi.get("paths", {})
            results: List[Dict[str, Any]] = []
            status_counts: Dict[int, int] = {}
            server_errors: List[Dict[str, Any]] = []

            dummy_uuid = str(uuid.uuid4())
            path_subs = {
                "{task_id}": dummy_uuid,
                "{exam_id}": "upsc_cse",
                "{roadmap_id}": dummy_uuid,
                "{document_id}": dummy_uuid,
                "{session_id}": dummy_uuid,
                "{notification_id}": dummy_uuid,
                "{item_id}": dummy_uuid,
            }

            custom_payloads = {
                "/api/v1/search/hybrid": {"query": "machine learning", "top_k": 3},
                "/api/v1/search/semantic": {"query": "machine learning", "top_k": 3},
                "/api/v1/settings/ai-mode": {"mode": "balanced"},
                "/api/v1/sync/push": {"items": []},
                "/api/v1/teaching/start": {"topic": "Operating Systems", "subject": "CS"},
                "/api/v1/planner/plans": {"subject": "Polity", "target_exam_date": "2026-12-01"},
                "/api/v1/tutor/ask": {"query": "What is virtual memory?"},
                "/api/v1/exams/configs": {"exam_type": "upsc_prelims", "title": "GS Paper 1 Mock", "total_questions": 10},
                "/api/v1/competitive-exams/profile": {"target_exam": "UPSC_CSE", "optional_subject": "PSIR"},
                "/api/v1/users/profile": {"full_name": "QA Updated"},
                "/api/v1/users/settings": {"theme_mode": "dark"},
                "/api/v1/voice/chat": {"message": "Hello study buddy"},
                "/api/v1/voice/synthesize": {"text": "Hello world", "voice": "standard"},
                "/api/v1/voice/transcribe": {"audio_base64": ""},
                "/api/v1/agent/chat": {"message": "What is next on my schedule?"},
                "/api/v1/agent/evaluate-state": {"state": {}},
                "/api/v1/competitive-exams/answer-writing/evaluate": {
                    "question": "Discuss the significance of Article 21.",
                    "student_answer": "Article 21 protects life and personal liberty.",
                    "word_limit": 250
                },
                "/api/v1/competitive-exams/mock/adaptive": {"exam_type": "UPSC_PRELIMS", "subject": "Polity"},
                "/api/v1/curriculum/learning-pack/generate": {"subject": "Operating Systems", "topic": "Deadlocks"},
                "/api/v1/curriculum/roadmap/generate": {"subject": "Computer Science"},
                "/api/v1/revision/submit": {"card_id": dummy_uuid, "rating": 4},
                "/api/v1/practice/sessions/start": {"subject": "CS", "topics": ["Deadlocks"]},
                "/api/v1/multimodal/analyze": {
                    "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                    "image_filename": "sample.png",
                    "user_prompt": "Explain this diagram",
                    "current_topic": "OS",
                },
            }

            for path, methods in sorted(paths.items()):
                for method, spec in methods.items():
                    if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                        continue

                    actual_path = path
                    for param, val in path_subs.items():
                        actual_path = actual_path.replace(param, val)

                    payload = custom_payloads.get(path, {})
                    try:
                        if method.lower() == "get":
                            resp = await client.get(actual_path, headers=auth_headers)
                        elif method.lower() == "post":
                            resp = await client.post(actual_path, json=payload, headers=auth_headers)
                        elif method.lower() == "put":
                            resp = await client.put(actual_path, json=payload, headers=auth_headers)
                        elif method.lower() == "delete":
                            resp = await client.delete(actual_path, headers=auth_headers)
                        elif method.lower() == "patch":
                            resp = await client.patch(actual_path, json=payload, headers=auth_headers)

                        code = resp.status_code
                        status_counts[code] = status_counts.get(code, 0) + 1
                        is_5xx = 500 <= code <= 599

                        if is_5xx:
                            server_errors.append({
                                "method": method.upper(),
                                "path": actual_path,
                                "status": code,
                                "response": resp.text[:200],
                            })

                        results.append({
                            "method": method.upper(),
                            "path": actual_path,
                            "status": code,
                            "is_5xx": is_5xx,
                        })

                    except Exception as e:
                        server_errors.append({
                            "method": method.upper(),
                            "path": actual_path,
                            "status": "EXCEPTION",
                            "response": str(e),
                        })

            print("\n" + "=" * 80)
            print("ENDPOINT SMOKE TEST RESULTS")
            print(f"Total Routes Tested: {len(results)}")
            print(f"Status Code Breakdown: {dict(sorted(status_counts.items()))}")
            print(f"5xx Server Errors Encountered: {len(server_errors)}")
            print("=" * 80)

            for res in results:
                tag = "FAIL 5XX" if res["is_5xx"] else "PASS OK "
                print(f"[{tag}] {res['method']:<6} {res['path']:<55} -> {res['status']}")

            if server_errors:
                print("\n" + "=" * 80)
                print("SERVER ERRORS (5XX) DETECTED:")
                for err in server_errors:
                    print(f"  - {err['method']} {err['path']}: {err['status']} -> {err['response']}")
                print("=" * 80)
            else:
                print("\n>> VERIFIED: ZERO 5xx ERRORS across all API endpoints!")

            return results, server_errors


if __name__ == "__main__":
    asyncio.run(run_endpoint_smoke_tests())
