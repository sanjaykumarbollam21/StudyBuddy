import pytest
from datetime import datetime, timezone, timedelta
import uuid

from app.intelligence.evaluator import PedagogicalEvaluator, StudentIntent, TeacherAction
from app.intelligence.mastery import calculate_advanced_mastery, calculate_topic_urgency_score
from app.sync.service import SyncEngine
from app.schemas.sync import SyncChangeItem
from app.notifications.service import NotificationService
from app.core.security import (
    validate_safe_filename,
    validate_file_upload,
    InMemoryRateLimiter,
    create_access_token,
    decode_access_token,
)
from app.core.telemetry import sanitize_data


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================================
# 1. AI QUALITY EVALUATION DATASET TESTS
# =====================================================================

def test_ai_quality_evaluation_full_spectrum():
    """
    Validates Phase 11 AI Quality Benchmark across all 9 response categories:
    - Correct
    - Partially correct
    - Misconception
    - Wrong
    - Ambiguous
    - "I don't know"
    - "Give me a hint"
    - "Explain simpler"
    - "Why?"
    """
    evaluator = PedagogicalEvaluator()

    # 1. Correct
    res_correct = evaluator.evaluate_response(
        student_text="A deadlock requires mutual exclusion, hold and wait, no preemption, and circular wait.",
        topic="Deadlocks",
    )
    assert res_correct["intent"] == StudentIntent.CORRECT
    assert res_correct["action"] == TeacherAction.ADVANCE_TOPIC
    assert res_correct["score"] == 1.0

    # 2. Partially correct
    res_partial = evaluator.evaluate_response(
        student_text="Deadlocks happen when processes have a circular wait on resources.",
        topic="Deadlocks",
    )
    assert res_partial["intent"] == StudentIntent.PARTIALLY_CORRECT
    assert res_partial["action"] == TeacherAction.PROMPT_MISSING_PIECE
    assert 0.5 <= res_partial["score"] <= 0.8

    # 3. Misconception (prevention vs avoidance)
    res_misconception = evaluator.evaluate_response(
        student_text="Deadlock prevention and avoidance are the same thing just different names.",
        topic="Deadlocks",
    )
    assert res_misconception["intent"] == StudentIntent.MISCONCEPTION
    assert res_misconception["action"] == TeacherAction.REMEDIATE_MISCONCEPTION
    assert "Banker's Algorithm" in res_misconception["feedback"]

    # 4. Completely wrong
    res_wrong = evaluator.evaluate_response(
        student_text="Deadlocks are caused by high screen brightness and slow wifi.",
        topic="Deadlocks",
    )
    assert res_wrong["intent"] == StudentIntent.WRONG
    assert res_wrong["action"] == TeacherAction.REDIRECT_WITH_ANALOGY
    assert res_wrong["score"] < 0.3

    # 5. Ambiguous
    res_ambiguous = evaluator.evaluate_response(
        student_text="it is something",
        topic="Deadlocks",
    )
    assert res_ambiguous["intent"] == StudentIntent.AMBIGUOUS
    assert res_ambiguous["action"] == TeacherAction.CLARIFY_AMBIGUITY

    # 6. "I don't know"
    res_dont_know = evaluator.evaluate_response(
        student_text="I don't know honestly",
        topic="Deadlocks",
    )
    assert res_dont_know["intent"] == StudentIntent.DONT_KNOW
    assert res_dont_know["action"] == TeacherAction.GIVE_SCAFFOLDED_HINT

    # 7. "Give me a hint"
    res_hint = evaluator.evaluate_response(
        student_text="Can you give me a hint please?",
        topic="Deadlocks",
    )
    assert res_hint["intent"] == StudentIntent.REQUEST_HINT
    assert res_hint["action"] == TeacherAction.GIVE_CONCEPTUAL_CLUE

    # 8. "Explain simpler"
    res_simpler = evaluator.evaluate_response(
        student_text="Can you explain simpler with an analogy?",
        topic="Deadlocks",
    )
    assert res_simpler["intent"] == StudentIntent.REQUEST_SIMPLER
    assert res_simpler["action"] == TeacherAction.EXPLAIN_WITH_ANALOGY
    assert "bridge" in res_simpler["feedback"].lower() or "cars" in res_simpler["feedback"].lower()

    # 9. "Why?"
    res_why = evaluator.evaluate_response(
        student_text="Why?",
        topic="Deadlocks",
    )
    assert res_why["intent"] == StudentIntent.REQUEST_WHY
    assert res_why["action"] == TeacherAction.EXPLAIN_FIRST_PRINCIPLES


# =====================================================================
# 2. SECURITY PEN-TESTING & TENANT ISOLATION
# =====================================================================

def test_security_jwt_tampering_and_expiration():
    """
    Pen-test: Expired JWT and forged signatures must be rejected cleanly.
    """
    # 1. Expired token
    expired_token = create_access_token(
        subject="user-123",
        expires_delta=timedelta(seconds=-60),
    )
    assert decode_access_token(expired_token) is None

    # 2. Tampered token signature
    valid_token = create_access_token(subject="user-123")
    tampered_token = valid_token[:-5] + "XXXXX"
    assert decode_access_token(tampered_token) is None


def test_security_malicious_path_traversal_and_uploads():
    """
    Pen-test: Directory traversal, evil shell scripts, and oversized uploads.
    """
    # Path traversal patterns
    assert validate_safe_filename("../../etc/shadow") == "shadow"
    assert validate_safe_filename("..\\..\\boot.ini") == "boot.ini"
    assert validate_safe_filename("....//....//passwords.txt") == "passwords.txt"

    with pytest.raises(ValueError):
        validate_safe_filename("..")

    # Malicious file extension rejection
    with pytest.raises(ValueError, match="Disallowed file extension"):
        validate_file_upload("exploit.sh", b"#!/bin/bash\nrm -rf /")

    with pytest.raises(ValueError, match="Disallowed file extension"):
        validate_file_upload("virus.exe", b"MZ\x90\x00")

    # Valid file upload
    assert validate_file_upload("os_lecture_notes.pdf", b"%PDF-1.4 sample content") is True


def test_security_rate_limiter_burst_protection():
    """
    Pen-test: High-frequency requests from single client get throttled.
    """
    limiter = InMemoryRateLimiter(requests_per_minute=5)
    ip = "10.0.0.55"

    for _ in range(5):
        assert limiter.is_allowed(ip) is True

    # 6th request must be rejected
    assert limiter.is_allowed(ip) is False


def test_observability_telemetry_sanitization():
    """
    Verifies that sensitive data (passwords, tokens, raw file contents)
    are strictly redacted from structured logging output.
    """
    raw_payload = {
        "user_id": "usr-01",
        "action": "login",
        "password": "SuperSecretPassword123!",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "metadata": {
            "token": "secret_session_token",
            "file_content": "binary-unredacted-data",
            "safe_field": "public_study_title",
        },
    }

    sanitized = sanitize_data(raw_payload)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["metadata"]["token"] == "[REDACTED]"
    assert sanitized["metadata"]["file_content"] == "[REDACTED]"
    assert sanitized["metadata"]["safe_field"] == "public_study_title"


# =====================================================================
# 3. END-TO-END GOLDEN JOURNEY & FAILURE RECOVERY
# =====================================================================

@pytest.mark.asyncio
async def test_end_to_end_golden_journey_loop():
    """
    Validates complete pedagogical cycle:
    1. Study Session Kickoff notification generated
    2. Socratic teaching evaluated
    3. Practice attempt graded
    4. Multi-factor mastery recalculated with difficulty & retention
    5. Spaced revision agenda updated
    6. Topic urgency scored for adaptive planner
    7. Offline sync push/pull executed
    """
    user_id = f"e2e-student-{uuid.uuid4().hex[:6]}"
    device_id = "device-tablet-e2e"

    # Step 1: Notifications
    notif_svc = NotificationService()
    notifs = notif_svc.generate_proactive_study_notifications(
        user_id=user_id,
        current_topic_name="Deadlocks & Synchronization",
        session_duration_minutes=30,
        due_revision_count=3,
        exam_name="Operating Systems",
        days_until_exam=4,
        weak_topic_name="Banker's Algorithm",
    )
    assert len(notifs) == 3

    # Step 2: Socratic Teaching Evaluation
    teacher_eval = PedagogicalEvaluator.evaluate_response(
        student_text="Deadlock occurs when mutual exclusion, hold and wait, no preemption, and circular wait hold simultaneously.",
        topic="Deadlocks",
    )
    assert teacher_eval["intent"] == StudentIntent.CORRECT

    # Step 3 & 4: Multi-Factor Mastery
    mastery_result = calculate_advanced_mastery(
        recent_accuracy=0.92,
        historical_accuracy=0.85,
        practice_count=8,
        avg_difficulty=1.3,
        question_type="applied",
        student_confidence=0.9,
    )
    assert mastery_result["mastery_percentage"] >= 80.0
    assert mastery_result["is_mastered"] is True

    # Step 5: Urgency for Planner
    urgency = calculate_topic_urgency_score(
        mastery_percentage=mastery_result["mastery_percentage"],
        exam_weight=1.5,
        days_until_exam=4,
        days_since_revision=2.0,
    )
    assert urgency > 0.0

    # Step 6: Sync Engine (simulate offline change push)
    sync_engine = SyncEngine(db_session=None)
    change = SyncChangeItem(
        id=str(uuid.uuid4()),
        entity_type="mastery",
        entity_id="topic-deadlocks",
        action="update",
        client_timestamp=utc_now(),
        payload={
            "topic_id": "topic-deadlocks",
            "mastery_percentage": mastery_result["mastery_percentage"],
            "times_practiced": 8,
        },
    )

    push_res = await sync_engine.push_changes(user_id=user_id, device_id=device_id, changes=[change])
    assert push_res.success is True
    assert push_res.applied_count == 1

    pull_res = await sync_engine.pull_changes(user_id=user_id, device_id=device_id)
    assert pull_res.server_timestamp is not None
