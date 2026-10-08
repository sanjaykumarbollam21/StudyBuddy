import pytest
from app.revision.sm2 import SM2Scheduler
from app.revision.service import RevisionService
from app.models.user import User


def test_sm2_interval_progression_and_lapse():
    # 1. First successful recall (q=4)
    step1 = SM2Scheduler.calculate_sm2(quality=4, repetition_count=0, interval_days=0, ease_factor=2.5)
    assert step1["repetition_count"] == 1
    assert step1["interval_days"] == 1
    assert step1["is_passed"] is True

    # 2. Second successful recall (q=5)
    step2 = SM2Scheduler.calculate_sm2(quality=5, repetition_count=1, interval_days=1, ease_factor=step1["ease_factor"])
    assert step2["repetition_count"] == 2
    assert step2["interval_days"] == 6
    assert step2["is_passed"] is True
    assert step2["ease_factor"] >= 2.5

    # 3. Third successful recall (q=4)
    step3 = SM2Scheduler.calculate_sm2(quality=4, repetition_count=2, interval_days=6, ease_factor=step2["ease_factor"])
    assert step3["repetition_count"] == 3
    assert step3["interval_days"] >= 15

    # 4. Failed recall / lapse (q=2)
    step4 = SM2Scheduler.calculate_sm2(quality=2, repetition_count=3, interval_days=15, ease_factor=step3["ease_factor"])
    assert step4["repetition_count"] == 0
    assert step4["interval_days"] == 1
    assert step4["is_passed"] is False


def test_hardened_mastery_trajectory_and_forgetting_decay():
    # Case A: Improving trajectory [40, 60, 80, 100] (upward momentum)
    score_improving = SM2Scheduler.calculate_hardened_mastery(
        current_mastery=80.0,
        quality_history=[2, 3, 4, 5],
        latest_quality=5,
        days_since_last_recall=1,
        consecutive_successes=3,
    )

    # Case B: Stagnant or regressing trajectory [80, 80, 60, 40]
    score_regressing = SM2Scheduler.calculate_hardened_mastery(
        current_mastery=60.0,
        quality_history=[4, 4, 3, 2],
        latest_quality=2,
        days_since_last_recall=1,
        consecutive_successes=0,
    )

    # Hardened mastery must distinctly favor upward learning over regression
    assert score_improving > score_regressing
    assert score_improving >= 85.0

    # Test time decay: Overdue for 14 days without recall
    score_fresh = SM2Scheduler.calculate_hardened_mastery(
        current_mastery=80.0,
        quality_history=[4],
        latest_quality=4,
        days_since_last_recall=1,
    )
    score_decayed = SM2Scheduler.calculate_hardened_mastery(
        current_mastery=80.0,
        quality_history=[4],
        latest_quality=4,
        days_since_last_recall=14,  # Overdue by 11 days
    )
    assert score_decayed < score_fresh, "Memory decay factor must lower score when recall is neglected"


@pytest.mark.asyncio
async def test_revision_service_workflow(db_session):
    user = User(
        id="user-rev-test-1",
        email="rev_student@example.com",
        full_name="Revision Student",
        hashed_password="pw_test_fake",
    )
    db_session.add(user)
    await db_session.commit()

    service = RevisionService(db_session)

    # 1. Fetch due reviews (auto-seeds initial deck)
    due_items = await service.get_due_reviews(user.id, limit=5)
    assert len(due_items) >= 2
    first_item = due_items[0]
    assert "retrieval_prompt" in first_item
    assert "Deadlocks" in first_item["topic_title"] or len(first_item["topic_title"]) > 0

    # 2. Submit high quality recall (q=4)
    res_pass = await service.submit_review(
        user_id=user.id,
        item_id=first_item["id"],
        quality_rating=4,
        student_recall="Mutual exclusion, hold and wait, no preemption, circular wait.",
    )
    assert res_pass["is_passed"] is True
    assert res_pass["new_interval_days"] >= 1
    assert res_pass["updated_mastery_percentage"] >= 60.0

    # 3. Fetch daily agenda ("Today's Learning")
    agenda = await service.get_daily_agenda(user.id)
    assert "continue_learning" in agenda
    assert "due_for_review_count" in agenda
    assert "top_weak_area" in agenda
    assert "recommended_action" in agenda
    assert "exam_priority" in agenda


@pytest.mark.asyncio
async def test_revision_api_endpoints(client, db_session):
    # Signup user
    reg = await client.post(
        "/api/v1/auth/signup",
        json={"email": "api_rev_user@example.com", "password": "Password123!", "full_name": "API Revisor"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get due reviews
    due_res = await client.get("/api/v1/revision/due", headers=headers)
    assert due_res.status_code == 200
    items = due_res.json()
    assert len(items) >= 1
    item_id = items[0]["id"]

    # 2. Submit active recall review
    sub_res = await client.post(
        "/api/v1/revision/submit",
        json={"item_id": item_id, "quality_rating": 5},
        headers=headers,
    )
    assert sub_res.status_code == 200
    data = sub_res.json()
    assert data["is_passed"] is True
    assert data["new_interval_days"] >= 1

    # 3. Get daily agenda
    agenda_res = await client.get("/api/v1/revision/agenda", headers=headers)
    assert agenda_res.status_code == 200
    ag_data = agenda_res.json()
    assert ag_data["due_for_review_count"] >= 0
    assert "topic" in ag_data["continue_learning"]
