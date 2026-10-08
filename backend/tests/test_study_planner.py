import pytest
from datetime import datetime, timezone, timedelta

from app.planner.engine import StudyPlannerEngine
from app.planner.agent import StudyAgentService
from app.models.planner import StudyPlan, StudyPlanItem


def utc_now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_plan_synthesis():
    """
    Verifies multi-phase plan generation with curriculum DAG,
    mastery weighting, and balanced phase distribution.
    """
    engine = StudyPlannerEngine(db_session=None)
    plan = await engine.create_plan(
        user_id="user-test-planner-1",
        title="Operating Systems Semester Prep",
        subject="Operating Systems",
        days_until_exam=12,
        daily_study_minutes=120,
    )

    assert plan.id is not None
    assert plan.total_days == 12
    assert plan.daily_study_minutes == 120
    assert plan.total_available_hours == 24.0
    assert plan.current_day == 1
    assert plan.status == "active"

    # Strategy breakdown validation
    strategy = plan.strategy_summary
    assert "phases" in strategy
    assert len(strategy["phases"]) == 4
    assert strategy["total_days"] == 12
    assert strategy["total_available_hours"] == 24.0

    # Scheduled item checks
    assert len(plan.items) > 12
    # Verify Phase 1 starts with high-yield weak areas (Deadlocks or Concurrency)
    first_item = plan.items[0]
    assert first_item.day_number == 1
    assert first_item.session_type == "learn"
    assert "Deadlocks" in first_item.topic or "Process" in first_item.topic

    # Verify Mock Exam is scheduled near end of trajectory
    mock_items = [it for it in plan.items if it.session_type == "mock_exam"]
    assert len(mock_items) >= 1
    assert mock_items[0].day_number >= 9


@pytest.mark.asyncio
async def test_dynamic_replan_on_missed_day():
    """
    Verifies continuous dynamic re-planning on missed days:
    Does NOT fail the student, redistributes remaining load, and updates rationale.
    """
    engine = StudyPlannerEngine(db_session=None)
    plan = await engine.create_plan(
        user_id="user-test-planner-2",
        days_until_exam=12,
        daily_study_minutes=120,
    )

    # Simulate student missing 2 days
    replanned = await engine.replan(
        plan_id=plan.id,
        user_id="user-test-planner-2",
        missed_days=2,
        reason="Missed weekend study sessions",
    )

    assert replanned.current_day == 3
    # Remaining days should be 12 - 3 + 1 = 10
    remaining_days = replanned.total_days - replanned.current_day + 1
    assert remaining_days == 10
    assert replanned.total_available_hours == (10 * 120) / 60.0  # 20.0 hours
    assert "Absorbed 2 missed day(s)" in replanned.strategy_summary["rationale"]

    # Verify that scheduled items still contain final mock exam
    mock_items = [it for it in replanned.items if it.session_type == "mock_exam"]
    assert len(mock_items) >= 1


@pytest.mark.asyncio
async def test_micro_session_optimization():
    """
    Verifies that time constraints (15 mins vs 30 mins vs 60 mins)
    select the optimal pedagogical learning modality.
    """
    engine = StudyPlannerEngine(db_session=None)

    # 15 minutes -> Active Recall
    session_15 = await engine.generate_micro_session(
        user_id="user-test-micro",
        minutes=15,
        subject="Operating Systems",
    )
    assert session_15["allocated_minutes"] == 15
    assert session_15["action_type"] == "active_recall"
    assert "active recall" in session_15["pedagogical_reasoning"].lower()

    # 30 minutes -> 15-question targeted drill
    session_30 = await engine.generate_micro_session(
        user_id="user-test-micro",
        minutes=30,
        subject="Operating Systems",
    )
    assert session_30["allocated_minutes"] == 30
    assert session_30["action_type"] == "practice_quiz"
    assert session_30["action_payload"]["question_count"] == 15

    # 60 minutes -> Socratic Lesson deep dive
    session_60 = await engine.generate_micro_session(
        user_id="user-test-micro",
        minutes=60,
        subject="Operating Systems",
    )
    assert session_60["allocated_minutes"] == 60
    assert session_60["action_type"] == "socratic_lesson"
    assert "socratic teacher" in session_60["pedagogical_reasoning"].lower()


@pytest.mark.asyncio
async def test_agent_conversational_task_layer():
    """
    Verifies the proactive Study Agent understanding and executing
    student intentions and routing directly to action payloads.
    """
    agent = StudyAgentService(db_session=None)

    # 1. "Plan my preparation"
    res1 = await agent.process_student_message(
        user_id="user-test-agent",
        message="I have my OS exam in 12 days and can study 2 hours every day.",
    )
    assert res1.intent == "plan_preparation"
    assert "24 total study hours" in res1.message
    assert res1.suggested_action is not None
    assert res1.suggested_action.action_type == "socratic_lesson"

    # 2. "I have 30 minutes"
    res2 = await agent.process_student_message(
        user_id="user-test-agent",
        message="I have 30 minutes right now.",
    )
    assert res2.intent == "micro_session"
    assert res2.suggested_action is not None
    assert res2.suggested_action.duration_minutes == 30
    assert res2.suggested_action.action_type == "practice_quiz"

    # 3. "I missed yesterday's study session"
    res3 = await agent.process_student_message(
        user_id="user-test-agent",
        message="I missed yesterday's study session.",
    )
    assert res3.intent == "handle_missed_day"
    assert "No Problem — Schedule Re-calculated!" in res3.message
    assert res3.suggested_action is not None

    # 4. "Move my exam to next Monday" (7 days)
    res4 = await agent.process_student_message(
        user_id="user-test-agent",
        message="Move my exam: 7 days left.",
    )
    assert res4.intent == "reschedule_exam"
    assert "Exam Date Updated!" in res4.message

    # 5. "Focus more on the topics I'm weak at"
    res5 = await agent.process_student_message(
        user_id="user-test-agent",
        message="Focus more on the topics I'm weak at.",
    )
    assert res5.intent == "focus_weak_areas"
    assert "Weak-Area Prioritization Engaged!" in res5.message
    assert res5.suggested_action.action_type == "socratic_lesson"

    # 6. "Start a 20-question practice session"
    res6 = await agent.process_student_message(
        user_id="user-test-agent",
        message="Start a 20-question practice session.",
    )
    assert res6.intent == "execute_action"
    assert res6.suggested_action.action_type == "practice_quiz"
    assert res6.suggested_action.metadata["question_count"] == 20

    # 7. "Test whether I'm ready for the exam"
    res7 = await agent.process_student_message(
        user_id="user-test-agent",
        message="Test whether I'm ready for the exam.",
    )
    assert res7.intent == "execute_action"
    assert res7.suggested_action.action_type == "mock_exam"
    assert res7.suggested_action.duration_minutes == 60

    # 8. "What should I study now?"
    res8 = await agent.process_student_message(
        user_id="user-test-agent",
        message="What should I study now?",
    )
    assert res8.intent == "what_next"
    assert res8.suggested_action is not None
