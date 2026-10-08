import pytest
import socket
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.teaching.engine import TeachingEngine
from app.teaching.state import TeachingState, EvaluationVerdict
from app.tutor.providers.local import LocalLLMProvider
from app.tutor.providers.mock import MockLLMProvider

@pytest.mark.asyncio
async def test_full_acceptance_teaching_loop_correct_path():
    """
    Acceptance Test Scenario:
    1. Student: "Teach me deadlocks"
    2. Teacher: "Before we start, what do you already know about deadlocks?"
    3. Student: "I think it happens when a process gets stuck."
    4. Teacher: Teaches concept + Two keys analogy + asks "Why can't either process continue?"
    5. Student: "Because each one is waiting for something the other one has."
    6. Teacher: Evaluates as CORRECT -> Mastery increases -> Advances to Coffman conditions.
    """
    engine = TeachingEngine(llm_provider=MockLLMProvider())

    # 1. Start teaching session
    turn1 = await engine.start_session(
        user_id="test-student-1",
        topic="Deadlocks",
    )
    assert turn1.state == TeachingState.ASSESS_PRIOR_KNOWLEDGE
    assert "what do you already know about deadlocks" in turn1.teacher_message.lower()

    # 2. Student shares initial intuition
    turn2 = await engine.process_student_turn(
        session_id=turn1.session_id,
        student_answer="I think it happens when a process gets stuck.",
    )
    assert turn2.state == TeachingState.CHECK_UNDERSTANDING
    assert "Good starting point" in turn2.teacher_message
    assert "two people each holding one key" in turn2.teacher_message.lower()
    assert "Why can't either process continue?" in turn2.check_question

    # 3. Student answers check question correctly
    turn3 = await engine.process_student_turn(
        session_id=turn1.session_id,
        student_answer="Because each one is waiting for something the other one has.",
    )
    # Evaluated as correct and advanced to next concept
    assert turn3.evaluation is not None
    assert turn3.evaluation["is_correct"] is True
    assert turn3.mastery_percentage > 0.0
    assert turn3.current_step_number == 2
    assert "Coffman" in turn3.concept_title or "Four Conditions" in turn3.concept_title
    assert "Next, let's look at" in turn3.teacher_message

@pytest.mark.asyncio
async def test_full_acceptance_teaching_loop_misconception_and_remediation():
    """
    Acceptance Test Scenario (Adaptive Remediation):
    1. Student answers check question with a misconception: "Deadlock happens because the CPU is too slow."
    2. Teacher diagnoses misconception -> Reteaches with simpler analogy -> Probes with simpler question.
    3. Student answers simpler probe: "Neither can continue."
    4. Teacher confirms understanding -> Advances.
    """
    engine = TeachingEngine(llm_provider=MockLLMProvider())

    # Start and move past assessment
    start = await engine.start_session(user_id="test-student-2", topic="Deadlocks")
    await engine.process_student_turn(session_id=start.session_id, student_answer="Not much.")

    # Student states misconception
    remed_turn = await engine.process_student_turn(
        session_id=start.session_id,
        student_answer="Deadlock happens because the CPU is too slow.",
    )
    assert remed_turn.state == TeachingState.RETEACHING
    assert remed_turn.evaluation["is_correct"] is False
    assert "performance" in remed_turn.teacher_message.lower()
    assert "simplify it" in remed_turn.teacher_message.lower()

    # Student now answers the simpler probe
    advance_turn = await engine.process_student_turn(
        session_id=start.session_id,
        student_answer="Neither can continue.",
    )
    assert advance_turn.evaluation["is_correct"] is True
    assert advance_turn.current_step_number == 2

@pytest.mark.asyncio
async def test_teaching_api_endpoints_end_to_end(client: AsyncClient):
    """
    Test the FastAPI /api/v1/teaching endpoints with authenticated student.
    """
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "teaching_student@example.com", "password": "Password123!", "full_name": "Teaching Student"},
    )
    student_token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Start teaching
    start_resp = await client.post(
        "/api/v1/teaching/start",
        headers=headers,
        json={"topic": "Deadlocks", "subject": "Operating Systems"},
    )
    assert start_resp.status_code == 200
    data = start_resp.json()
    session_id = data["session_id"]
    assert "what do you already know" in data["teacher_message"].lower()

    # 2. Interact - Prior knowledge
    turn1_resp = await client.post(
        f"/api/v1/teaching/{session_id}/interact",
        headers=headers,
        json={"answer": "Processes get blocked waiting for resources."},
    )
    assert turn1_resp.status_code == 200
    data1 = turn1_resp.json()
    assert data1["check_question"] is not None

    # 3. Interact - Check answer
    turn2_resp = await client.post(
        f"/api/v1/teaching/{session_id}/interact",
        headers=headers,
        json={"answer": "Because each process is waiting for what the other holds."},
    )
    assert turn2_resp.status_code == 200
    data2 = turn2_resp.json()
    assert data2["evaluation"]["is_correct"] is True

    # 4. Get session status
    get_resp = await client.get(
        f"/api/v1/teaching/{session_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    session_data = get_resp.json()
    assert session_data["session_id"] == session_id
    assert len(session_data["dialogue"]) >= 4

@pytest.mark.asyncio
async def test_offline_local_llm_provider_guarantees_zero_network():
    """
    Verify LocalLLMProvider evaluates answers completely offline with blocked network.
    """
    orig_connect = socket.socket.connect

    def blocked_connect(self, *args, **kwargs):
        raise ConnectionRefusedError("Offline policy violation: Network connection prohibited!")

    socket.socket.connect = blocked_connect
    try:
        local_provider = LocalLLMProvider()
        result = await local_provider.evaluate_student_answer(
            concept_title="Deadlock Definition",
            question="Why can't either process continue?",
            expected_concept="each process is waiting for a resource held by another in circular wait",
            student_answer="Each one waits for the other process to release the resource.",
            common_misconceptions={"cpu speed": "CPU performance is not deadlock."},
        )
        assert result["verdict"] == "correct"
        assert result["confidence"] > 0.60
    finally:
        socket.socket.connect = orig_connect


@pytest.mark.asyncio
async def test_teaching_session_db_persistence_and_crud(db_session):
    """
    Verify TeachingSessionDB persistence, JSON serialization of steps & dialogue,
    and async CRUD operations via TeachingSessionService.
    """
    from datetime import datetime, timezone
    from app.models.user import User
    from app.teaching.service import TeachingSessionService
    from app.teaching.models import TeachingSessionModel
    from app.teaching.state import TeachingState, ConceptStep, StudentDialogueTurn

    # Create user for foreign key integrity
    user = User(
        id="test-student-persist-1",
        email="persist_1@example.com",
        hashed_password="pw",
        full_name="Persist Student 1",
    )
    db_session.add(user)
    await db_session.commit()

    # 1. Create a session model
    session_model = TeachingSessionModel(
        session_id="session-persist-100",
        user_id="test-student-persist-1",
        topic="Semaphores",
        subject="Operating Systems",
        current_state=TeachingState.CHECK_UNDERSTANDING,
        current_step_index=0,
        steps=[
            ConceptStep(
                step_index=0,
                title="Semaphore Basics",
                explanation="A signaling mechanism with wait and signal.",
                analogy="A bouncer at a club.",
                check_question="What does wait() do?",
                expected_core_concept="Decrements the counter and blocks if zero.",
            )
        ],
        dialogue=[
            StudentDialogueTurn(
                turn_index=0,
                speaker="teacher",
                state=TeachingState.ASSESS_PRIOR_KNOWLEDGE,
                content="What do you know about semaphores?",
            )
        ],
        mastery_score=25.0,
    )

    created = await TeachingSessionService.create_session(db_session, session_model)
    assert created.session_id == "session-persist-100"
    assert created.topic == "Semaphores"
    assert len(created.steps) == 1
    assert len(created.dialogue) == 1

    # 2. Retrieve session from DB
    retrieved = await TeachingSessionService.get_session(db_session, "session-persist-100")
    assert retrieved is not None
    assert retrieved.session_id == "session-persist-100"
    assert retrieved.mastery_score == 25.0
    assert retrieved.steps[0].title == "Semaphore Basics"
    assert retrieved.dialogue[0].speaker == "teacher"

    # 3. Update session (add dialogue turn and save)
    retrieved.dialogue.append(
        StudentDialogueTurn(
            turn_index=1,
            speaker="student",
            state=TeachingState.CHECK_UNDERSTANDING,
            content="It decrements the count.",
        )
    )
    retrieved.mastery_score = 50.0
    saved = await TeachingSessionService.save_session(db_session, retrieved)
    assert saved.mastery_score == 50.0
    assert len(saved.dialogue) == 2

    # Verify reload reflects updates
    reloaded = await TeachingSessionService.get_session(db_session, "session-persist-100")
    assert reloaded is not None
    assert len(reloaded.dialogue) == 2
    assert reloaded.dialogue[1].content == "It decrements the count."


@pytest.mark.asyncio
async def test_teaching_session_rehydration_after_restart(db_session):
    """
    Verify that sessions saved to the database survive memory wipes
    and are rehydrated on startup/demand.
    """
    from app.models.user import User
    from app.teaching.service import TeachingSessionService
    from app.teaching.models import TeachingSessionModel
    from app.teaching.engine import _active_sessions, TeachingEngine
    from app.teaching.state import TeachingState

    user = User(
        id="test-student-rehydrate",
        email="rehydrate@example.com",
        hashed_password="pw",
        full_name="Rehydrate Student",
    )
    db_session.add(user)
    await db_session.commit()

    sess = TeachingSessionModel(
        session_id="session-rehydrate-200",
        user_id="test-student-rehydrate",
        topic="Virtual Memory",
        current_state=TeachingState.TEACH_CONCEPT,
    )
    await TeachingSessionService.create_session(db_session, sess)

    # Simulate app server restart: clear all in-memory sessions
    _active_sessions.clear()
    assert "session-rehydrate-200" not in _active_sessions

    # 1. Test startup rehydration function
    rehydrated = await TeachingSessionService.rehydrate_active_sessions(db_session)
    assert "session-rehydrate-200" in rehydrated
    assert "session-rehydrate-200" in _active_sessions
    assert _active_sessions["session-rehydrate-200"].topic == "Virtual Memory"

    # 2. Clear again and test on-demand rehydration through TeachingEngine.get_session
    _active_sessions.clear()
    engine = TeachingEngine(db_session=db_session)
    fetched = await engine.get_session("session-rehydrate-200")
    assert fetched is not None
    assert fetched.session_id == "session-rehydrate-200"
    assert "session-rehydrate-200" in _active_sessions


@pytest.mark.asyncio
async def test_teaching_session_cleanup_stale_sessions(db_session):
    """
    Verify cleanup of incomplete sessions older than 24 hours
    while preserving fresh sessions and completed sessions.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.user import User
    from app.models.learning import TeachingSessionDB
    from app.teaching.service import TeachingSessionService

    user = User(
        id="test-student-cleanup",
        email="cleanup@example.com",
        hashed_password="pw",
        full_name="Cleanup Student",
    )
    db_session.add(user)
    await db_session.commit()

    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=36)
    recent_time = now - timedelta(hours=2)

    # 1. Stale incomplete session (>24h old) -> should be deleted
    stale_session = TeachingSessionDB(
        id="stale-session-1",
        user_id="test-student-cleanup",
        topic="Old Topic",
        is_completed=False,
        created_at=old_time,
        updated_at=old_time,
    )

    # 2. Recent incomplete session (2h old) -> should NOT be deleted
    recent_session = TeachingSessionDB(
        id="recent-session-2",
        user_id="test-student-cleanup",
        topic="Recent Topic",
        is_completed=False,
        created_at=recent_time,
        updated_at=recent_time,
    )

    # 3. Completed old session -> should NOT be deleted
    completed_old_session = TeachingSessionDB(
        id="completed-session-3",
        user_id="test-student-cleanup",
        topic="Completed Topic",
        is_completed=True,
        created_at=old_time,
        updated_at=old_time,
    )

    db_session.add_all([stale_session, recent_session, completed_old_session])
    await db_session.commit()

    # Run cleanup with 24h threshold
    deleted_count = await TeachingSessionService.cleanup_stale_sessions(db_session, older_than_hours=24)
    assert deleted_count == 1

    # Verify stale session is gone
    check_stale = await TeachingSessionService.get_session(db_session, "stale-session-1")
    assert check_stale is None

    # Verify recent and completed sessions are retained
    check_recent = await TeachingSessionService.get_session(db_session, "recent-session-2")
    assert check_recent is not None

    check_completed = await TeachingSessionService.get_session(db_session, "completed-session-3")
    assert check_completed is not None


@pytest.mark.asyncio
async def test_teaching_engine_db_backed_turn_progression(db_session):
    """
    Verify complete teaching loop runs with live db_session,
    persisting each turn into teaching_sessions table.
    """
    from app.models.user import User
    from app.teaching.service import TeachingSessionService

    user = User(
        id="test-student-loop",
        email="loop_student@example.com",
        hashed_password="pw",
        full_name="Loop Student",
    )
    db_session.add(user)
    await db_session.commit()

    engine = TeachingEngine(db_session=db_session, llm_provider=MockLLMProvider())

    # Turn 1: Start session -> DB record created
    turn1 = await engine.start_session(
        user_id="test-student-loop",
        topic="Deadlocks",
    )
    sess_id = turn1.session_id

    db_sess = await TeachingSessionService.get_session(db_session, sess_id)
    assert db_sess is not None
    assert db_sess.current_state == TeachingState.ASSESS_PRIOR_KNOWLEDGE
    assert len(db_sess.dialogue) == 1

    # Turn 2: Assess prior knowledge -> Transition and DB updated
    turn2 = await engine.process_student_turn(
        session_id=sess_id,
        student_answer="Processes get stuck waiting.",
    )
    db_sess2 = await TeachingSessionService.get_session(db_session, sess_id)
    assert db_sess2.current_state == TeachingState.CHECK_UNDERSTANDING
    assert len(db_sess2.dialogue) == 3  # teacher probe, student answer, teacher concept

    # Turn 3: Correct answer -> Mastery updated in DB
    turn3 = await engine.process_student_turn(
        session_id=sess_id,
        student_answer="Because each one is waiting for something the other one has.",
    )
    db_sess3 = await TeachingSessionService.get_session(db_session, sess_id)
    assert db_sess3.mastery_score > 0.0
    assert db_sess3.current_step_index == 1
    assert len(db_sess3.dialogue) >= 5
