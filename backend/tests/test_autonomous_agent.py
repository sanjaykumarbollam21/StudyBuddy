import pytest
from datetime import datetime, timezone
import uuid

from app.agent.decision import AgentDecisionEngine, ActionPermissionPolicy
from app.agent.orchestrator import AutonomousStudyAgent


def utc_now():
    return datetime.now(timezone.utc)


def test_agent_decision_engine_evaluation_and_allocation():
    """
    Test Phase 12 Agent Decision Engine:
    Evaluates student state across exam urgency, mastery gaps, and misconceptions,
    and intelligently allocates 60 minutes across Teacher, Practice, and Revision.
    """
    decision_engine = AgentDecisionEngine()

    result = decision_engine.evaluate_highest_value_task(
        available_minutes=60,
        days_until_exam=4,
        due_revision_count=3,
    )

    # 1. Goal and priority checks
    assert "Deadlocks" in result["goal"]
    assert result["priority"] == "critical"
    assert result["permission_level"] == "requires_permission"
    assert result["allocated_minutes"] == 60

    # 2. Orchestrated actions breakdown
    actions = result["proposed_actions"]
    assert len(actions) == 4

    engines = [a["engine"] for a in actions]
    assert "TeacherEngine" in engines
    assert "PracticeEngine" in engines
    assert "RevisionEngine" in engines
    assert "MasteryEngine" in engines

    # 3. Sum of durations equals available time (60 mins)
    total_duration = sum(a["duration_mins"] for a in actions)
    assert total_duration == 60


def test_agent_decision_short_session_allocation():
    """
    Test Phase 12 Agent Decision Engine for short 15-minute micro-session:
    Optimizes for rapid active recall revision.
    """
    decision_engine = AgentDecisionEngine()
    result = decision_engine.evaluate_highest_value_task(available_minutes=15)

    assert result["allocated_minutes"] == 15
    actions = result["proposed_actions"]
    assert len(actions) == 1
    assert actions[0]["engine"] == "RevisionEngine"
    assert actions[0]["duration_mins"] == 15


def test_safety_boundary_permission_classification():
    """
    Test Phase 12 Safety Policy:
    Ensures safe automatic vs confirmation-required actions are strictly segregated.
    """
    # Safe low-risk actions
    assert "generate_study_plan" in ActionPermissionPolicy.SAFE_AUTOMATIC
    assert "recalculate_plan" in ActionPermissionPolicy.SAFE_AUTOMATIC
    assert "create_practice_session" in ActionPermissionPolicy.SAFE_AUTOMATIC
    assert "schedule_revision" in ActionPermissionPolicy.SAFE_AUTOMATIC

    # High-impact actions requiring explicit student consent
    assert "start_remediation_session" in ActionPermissionPolicy.REQUIRES_PERMISSION
    assert "change_exam_goal" in ActionPermissionPolicy.REQUIRES_PERMISSION
    assert "delete_material" in ActionPermissionPolicy.REQUIRES_PERMISSION


@pytest.mark.asyncio
async def test_autonomous_agent_orchestrated_execution():
    """
    Test Phase 12 Orchestrator execution loop:
    Executes task, orchestrates existing engines, recalibrates mastery, and records completion.
    """
    user_id = f"agent-user-{uuid.uuid4().hex[:6]}"
    agent = AutonomousStudyAgent(db_session=None)

    # 1. Propose task
    proposed_task = await agent.evaluate_and_propose_task(
        user_id=user_id,
        available_minutes=60,
        days_until_exam=4,
    )
    assert proposed_task.id is not None
    assert proposed_task.current_state == "proposed"

    # 2. Execute task
    exec_res = await agent.execute_task(
        user_id=user_id,
        task_id=proposed_task.id,
        auto_apply_planner=True,
    )

    assert exec_res.success is True
    assert exec_res.current_state == "completed"
    assert len(exec_res.steps_executed) == 4
    assert exec_res.mastery_updated["mastery_percentage"] >= 80.0
    assert exec_res.planner_updated is True


def test_agent_decision_explainability():
    """
    Test Phase 12 Explainability:
    Answers 'Why did you choose this?' with transparent metrics.
    """
    agent = AutonomousStudyAgent(db_session=None)
    breakdown = {
        "top_topic": "Deadlocks & Synchronization",
        "mastery_percentage": 48.0,
        "exam_weight": 1.8,
        "days_until_exam": 4,
        "due_revisions": 3,
    }

    explanation = agent.explain_decision(breakdown)
    assert "48.0%" in explanation
    assert "1.8x" in explanation
    assert "4 days" in explanation
    assert "prevention and avoidance" in explanation


@pytest.mark.asyncio
async def test_agent_chat_conversational_turn():
    """
    Test Phase 12 Conversational Agent Orchestrator:
    Student asks: 'I have one hour. Prepare me for tomorrow's exam.'
    """
    user_id = f"agent-chat-user-{uuid.uuid4().hex[:6]}"
    agent = AutonomousStudyAgent(db_session=None)

    chat_res = await agent.chat_orchestrator(
        user_id=user_id,
        message="I have one hour. Prepare me for tomorrow's exam.",
        available_minutes=60,
    )

    assert chat_res.intent_detected == "autonomous_exam_prep"
    assert "Deadlocks" in chat_res.reply
    assert "60-minute" in chat_res.reply
    assert "TeacherEngine" in chat_res.orchestrated_engines
    assert chat_res.suggested_task is not None
    assert "explanation_text" in chat_res.explainability
