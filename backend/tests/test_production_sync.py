import pytest
from datetime import datetime, timezone, timedelta
import uuid

from app.intelligence.mastery import calculate_advanced_mastery, calculate_topic_urgency_score
from app.notifications.service import NotificationService, notification_service
from app.sync.service import SyncEngine
from app.schemas.sync import SyncChangeItem
from app.core.security import (
    validate_safe_filename,
    validate_file_upload,
    InMemoryRateLimiter,
)


def utc_now():
    return datetime.now(timezone.utc)


def test_advanced_mastery_calculation():
    """
    Test Phase 10.5 Learning Intelligence:
    Multi-factor mastery with difficulty, question type, retention decay, and gating.
    """
    # 1. High accuracy on hard applied questions with confidence
    res_high = calculate_advanced_mastery(
        recent_accuracy=0.95,
        historical_accuracy=0.90,
        practice_count=10,
        avg_difficulty=1.4,
        question_type="applied",
        mistake_recurrence_count=0,
        misconceptions_detected=0,
        days_since_last_recall=0.5,
        prerequisite_mastery=0.85,
        student_confidence=0.9,
    )
    assert res_high["mastery_percentage"] >= 85.0
    assert res_high["is_mastered"] is True
    assert res_high["gated_reason"] is None

    # 2. Prerequisite gating: weak prerequisite (<50%) caps mastery at 75%
    res_gated = calculate_advanced_mastery(
        recent_accuracy=1.0,
        historical_accuracy=1.0,
        practice_count=8,
        avg_difficulty=1.2,
        question_type="conceptual",
        prerequisite_mastery=0.40,  # Weak prerequisite
    )
    assert res_gated["mastery_percentage"] <= 75.0
    assert "prerequisite mastery" in res_gated["gated_reason"].lower()

    # 3. Repeated mistakes and misconceptions penalty
    res_penalized = calculate_advanced_mastery(
        recent_accuracy=0.70,
        historical_accuracy=0.65,
        practice_count=6,
        mistake_recurrence_count=4,
        misconceptions_detected=2,
    )
    assert res_penalized["mistake_penalty"] > 0
    assert res_penalized["misconception_penalty"] > 0
    assert res_penalized["mastery_percentage"] < res_high["mastery_percentage"]


def test_planner_urgency_optimization():
    """
    Test Phase 10.5 dynamic urgency calculation for topic prioritization.
    """
    # Urgent: low mastery, high exam weight, exam 3 days away
    urgent_score = calculate_topic_urgency_score(
        mastery_percentage=35.0,
        exam_weight=1.8,
        days_until_exam=3,
        days_since_revision=5.0,
        is_prerequisite_satisfied=True,
    )

    # Not urgent: high mastery, exam 40 days away
    low_urgency_score = calculate_topic_urgency_score(
        mastery_percentage=90.0,
        exam_weight=1.0,
        days_until_exam=40,
        days_since_revision=0.5,
        is_prerequisite_satisfied=True,
    )

    assert urgent_score > low_urgency_score
    assert urgent_score > 50.0


def test_notification_service():
    """
    Test Phase 10 proactive study alerts:
    session kickoff, spaced revision due, exam countdown.
    """
    svc = NotificationService()
    user_id = "test-user-prod-notif-1"

    notifications = svc.generate_proactive_study_notifications(
        user_id=user_id,
        current_topic_name="Deadlocks & Semaphores",
        session_duration_minutes=30,
        due_revision_count=4,
        exam_name="Operating Systems",
        days_until_exam=5,
        weak_topic_name="Synchronization",
    )

    assert len(notifications) == 3

    # Check session kickoff
    kickoff = next(n for n in notifications if n.category == "session_kickoff")
    assert "30-minute study session" in kickoff.message
    assert "Deadlocks & Semaphores" in kickoff.message

    # Check revision alert
    revision_alert = next(n for n in notifications if n.category == "revision_due")
    assert "4 revision items due today" in revision_alert.message

    # Check exam alert
    exam_alert = next(n for n in notifications if n.category == "exam_alert")
    assert "5 days away" in exam_alert.message
    assert "Synchronization is still below" in exam_alert.message

    # Mark as read
    assert kickoff.is_read is False
    success = svc.mark_as_read(user_id, kickoff.id)
    assert success is True
    assert kickoff.is_read is True


@pytest.mark.asyncio
async def test_offline_sync_engine():
    """
    Test Phase 10 offline sync engine push and pull handling.
    """
    engine = SyncEngine(db_session=None)
    user_id = "test-sync-user-1"
    device_id = "device-tablet-101"

    changes = [
        SyncChangeItem(
            id=str(uuid.uuid4()),
            entity_type="mastery",
            entity_id="topic-os-memory-management",
            action="update",
            client_timestamp=utc_now(),
            payload={"topic_id": "topic-os-memory-management", "mastery_percentage": 88.0, "times_practiced": 5},
            version=1,
        ),
        SyncChangeItem(
            id=str(uuid.uuid4()),
            entity_type="revision_item",
            entity_id="rev-item-001",
            action="update",
            client_timestamp=utc_now(),
            payload={"mastery_score": 0.9, "repetition_interval_days": 6},
            version=1,
        ),
    ]

    push_res = await engine.push_changes(user_id=user_id, device_id=device_id, changes=changes)
    assert push_res.success is True
    assert push_res.applied_count == 2
    assert push_res.conflict_count == 0

    pull_res = await engine.pull_changes(user_id=user_id, device_id=device_id)
    assert pull_res.server_timestamp is not None
    assert isinstance(pull_res.changes, list)


def test_security_hardening():
    """
    Test Phase 10 security: path traversal protection, upload validation, rate limiting.
    """
    # 1. Path traversal protection
    assert validate_safe_filename("notes.pdf") == "notes.pdf"
    assert validate_safe_filename("../../../etc/passwd.txt") == "passwd.txt"
    assert validate_safe_filename("..\\..\\windows\\system32\\calc.exe.pdf") == "calc.exe.pdf"

    with pytest.raises(ValueError):
        validate_safe_filename("..")

    # 2. File upload validation (extension & size)
    safe_bytes = b"Hello Study Buddy markdown content"
    assert validate_file_upload("syllabus.md", safe_bytes) is True

    with pytest.raises(ValueError, match="Disallowed file extension"):
        validate_file_upload("malicious.exe", safe_bytes)

    oversized_bytes = b"X" * 100
    with pytest.raises(ValueError, match="File size exceeds maximum"):
        validate_file_upload("big.pdf", oversized_bytes, max_size=50)

    # 3. Rate limiter
    limiter = InMemoryRateLimiter(requests_per_minute=3)
    client_ip = "192.168.1.100"
    assert limiter.is_allowed(client_ip) is True
    assert limiter.is_allowed(client_ip) is True
    assert limiter.is_allowed(client_ip) is True
    # 4th request should exceed limit
    assert limiter.is_allowed(client_ip) is False
