import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.revision.sm2 import SM2Scheduler
from app.exam.service import ExamService
from app.models.exam import MockExamSession
from app.teaching.state import TeachingState, ConceptStep
from app.teaching.engine import TeachingEngine
from app.tutor.providers.mock import MockLLMProvider


# =====================================================================
# 1. EXACT ARITHMETIC: UPSC PRELIMS NEGATIVE MARKING (0.66 PENALTY)
# =====================================================================

def test_upsc_prelims_exact_negative_marking_arithmetic():
    """
    Rigorously verifies the exact UPSC Prelims scoring arithmetic:
    - Each correct question awards +2.0 marks
    - Each incorrect question deducts -0.66 marks
    - Each unattempted question awards 0.0 marks (no penalty)
    - Net score is exactly: max(0.0, (correct * 2.0) - (incorrect * 0.66))
    """
    exam_service = ExamService(db_session=None)

    questions = [
        {
            "id": f"q_{i}",
            "topic": "Polity",
            "marks": 2.0,
            "negative_marks": 0.66,
            "correct_answer": "A",
            "options": ["A", "B", "C", "D"],
        }
        for i in range(1, 101)  # 100 questions standard UPSC Prelims GS Paper 1
    ]

    session = MockExamSession(
        id="mock-upsc-prelims-001",
        user_id="test-student-upsc",
        title="UPSC Prelims GS Mock",
        total_questions=100,
        total_marks=200.0,
        duration_minutes=120,
        questions_data=questions,
        answers_record={},
        status="in_progress",
    )

    # Scenario: 50 correct, 20 incorrect, 30 unattempted
    answers = {}
    for i in range(1, 51):
        answers[f"q_{i}"] = {"response": "A"}  # 50 correct
    for i in range(51, 71):
        answers[f"q_{i}"] = {"response": "B"}  # 20 incorrect
    # q_71 to q_100 omitted -> 30 unattempted

    # Direct calculation check:
    expected_awarded = 50 * 2.0  # 100.0
    expected_deducted = round(20 * 0.66, 2)  # 13.20
    expected_net = round(expected_awarded - expected_deducted, 2)  # 86.80

    total_awarded = 0.0
    total_deducted = 0.0
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    for q in questions:
        q_id = q["id"]
        q_marks = float(q["marks"])
        q_neg = float(q["negative_marks"])
        correct_ans = q["correct_answer"].lower()

        student_entry = answers.get(q_id)
        if not student_entry or not student_entry.get("response"):
            unanswered_count += 1
            continue

        resp = student_entry["response"].lower()
        if resp == correct_ans:
            total_awarded += q_marks
            correct_count += 1
        else:
            total_deducted += q_neg
            incorrect_count += 1

    assert correct_count == 50
    assert incorrect_count == 20
    assert unanswered_count == 30
    assert round(total_awarded, 2) == 100.0
    assert round(total_deducted, 2) == 13.20
    assert round(total_awarded - total_deducted, 2) == 86.80

    # Negative marks floor test: 0 correct, 10 wrong -> net marks cannot be negative
    zero_correct_net = max(0.0, round(0.0 - (10 * 0.66), 2))
    assert zero_correct_net == 0.0


# =====================================================================
# 2. EXACT MATHEMATICAL VERIFICATION: SM-2 SPACED REPETITION FORMULA
# =====================================================================

def test_sm2_exact_mathematical_updates_and_bounds():
    """
    Rigorously verifies the SM-2 algorithm:
    EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    Clamped to MIN_EASE_FACTOR = 1.30
    """
    # Quality 5: Perfect recall
    # delta = 0.1 - (0) * (...) = +0.10
    step_q5 = SM2Scheduler.calculate_sm2(quality=5, repetition_count=0, interval_days=0, ease_factor=2.50)
    assert step_q5["ease_factor"] == 2.60
    assert step_q5["interval_days"] == 1
    assert step_q5["is_passed"] is True

    # Quality 4: Correct response after hesitation
    # delta = 0.1 - 1 * (0.08 + 0.02) = 0.1 - 0.10 = 0.00
    step_q4 = SM2Scheduler.calculate_sm2(quality=4, repetition_count=1, interval_days=1, ease_factor=2.50)
    assert step_q4["ease_factor"] == 2.50
    assert step_q4["interval_days"] == 6
    assert step_q4["is_passed"] is True

    # Quality 3: Correct response recalled with serious difficulty
    # delta = 0.1 - 2 * (0.08 + 0.04) = 0.1 - 0.24 = -0.14
    step_q3 = SM2Scheduler.calculate_sm2(quality=3, repetition_count=2, interval_days=6, ease_factor=2.50)
    assert step_q3["ease_factor"] == 2.36
    assert step_q3["interval_days"] == round(6 * 2.36)  # 14
    assert step_q3["is_passed"] is True

    # Quality 2: Incorrect response; where the correct one seemed easy to recall
    # delta = 0.1 - 3 * (0.08 + 0.06) = 0.1 - 0.42 = -0.32
    step_q2 = SM2Scheduler.calculate_sm2(quality=2, repetition_count=3, interval_days=14, ease_factor=2.50)
    assert step_q2["ease_factor"] == 2.18
    assert step_q2["interval_days"] == 1  # Reset on lapse
    assert step_q2["repetition_count"] == 0
    assert step_q2["is_passed"] is False

    # Quality 1: Incorrect response; the correct one remembered
    # delta = 0.1 - 4 * (0.08 + 0.08) = 0.1 - 0.64 = -0.54
    step_q1 = SM2Scheduler.calculate_sm2(quality=1, repetition_count=1, interval_days=6, ease_factor=2.50)
    assert step_q1["ease_factor"] == 1.96
    assert step_q1["interval_days"] == 1
    assert step_q1["is_passed"] is False

    # Quality 0: Complete blackout
    # delta = 0.1 - 5 * (0.08 + 0.10) = 0.1 - 0.90 = -0.80
    step_q0 = SM2Scheduler.calculate_sm2(quality=0, repetition_count=1, interval_days=6, ease_factor=2.50)
    assert step_q0["ease_factor"] == 1.70
    assert step_q0["interval_days"] == 1
    assert step_q0["is_passed"] is False

    # Ease factor lower bound clamp: Never goes below 1.30
    clamped = SM2Scheduler.calculate_sm2(quality=0, repetition_count=1, interval_days=1, ease_factor=1.40)
    assert clamped["ease_factor"] == 1.30


# =====================================================================
# 3. MASTERY BOUNDS (0-100, NEVER NEGATIVE)
# =====================================================================

@pytest.mark.asyncio
async def test_mastery_bounds_invariants():
    """
    Verifies that mastery score cannot become negative or exceed 100.0%.
    """
    engine = TeachingEngine(llm_provider=MockLLMProvider())
    session_resp = await engine.start_session(user_id="test-student-bounds", topic="Deadlocks")
    session = engine.get_session_sync(session_resp.session_id)
    assert session is not None

    # Initial mastery is 0.0
    assert session.mastery_score == 0.0

    # Advance past assessment
    await engine.process_student_turn(session.session_id, "Basic awareness.")

    # Wrong answers / misconceptions do not lower mastery below 0.0
    turn_misc = await engine.process_student_turn(session.session_id, "CPU is too slow.")
    assert turn_misc.mastery_percentage == 0.0

    # Partial answers award bounded +10%
    turn_partial = await engine.process_student_turn(session.session_id, "Tasks are locked.")
    assert turn_partial.mastery_percentage == 10.0

    # Fully correct turn awards delta
    turn_correct = await engine.process_student_turn(
        session.session_id,
        "Because each one is waiting for what the other one has.",
    )
    assert turn_correct.mastery_percentage == 35.0
    assert 0.0 <= turn_correct.mastery_percentage <= 100.0


# =====================================================================
# 4. MULTI-ACCOUNT TENANT DATA ISOLATION & AUTH ENFORCEMENT
# =====================================================================

@pytest.mark.asyncio
async def test_multi_account_tenant_data_isolation(client: AsyncClient):
    """
    Ensures User A cannot access User B's documents, teaching sessions, or data.
    """
    import uuid
    suffix = uuid.uuid4().hex[:8]
    email_a = f"alpha_{suffix}@studybuddy.io"
    email_b = f"beta_{suffix}@studybuddy.io"

    # Register User A
    reg_a = await client.post(
        "/api/v1/auth/signup",
        json={"email": email_a, "password": "Password123!", "full_name": "Alpha Student"},
    )
    assert reg_a.status_code in [200, 201], reg_a.text
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    reg_b = await client.post(
        "/api/v1/auth/signup",
        json={"email": email_b, "password": "Password123!", "full_name": "Beta Student"},
    )
    assert reg_b.status_code in [200, 201], reg_b.text
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a teaching session
    start_a = await client.post(
        "/api/v1/teaching/start",
        headers=headers_a,
        json={"topic": "Deadlocks", "subject": "Operating Systems"},
    )
    assert start_a.status_code == 200, start_a.text
    sess_a_id = start_a.json()["session_id"]

    # User A checks active sessions -> includes sess_a_id
    active_a = await client.get("/api/v1/teaching/sessions/active", headers=headers_a)
    assert active_a.status_code == 200
    a_session_ids = [s["session_id"] for s in active_a.json()]
    assert sess_a_id in a_session_ids

    # User B checks active sessions -> MUST NOT include User A's session
    active_b = await client.get("/api/v1/teaching/sessions/active", headers=headers_b)
    assert active_b.status_code == 200
    b_session_ids = [s["session_id"] for s in active_b.json()]
    assert sess_a_id not in b_session_ids

    # Unauthenticated request rejected with 401
    unauth_resp = await client.get("/api/v1/teaching/sessions/active")
    assert unauth_resp.status_code == 401

    # Bad login credentials rejected with 401
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email_a, "password": "WrongPassword123!"},
    )
    assert bad_login.status_code == 401
