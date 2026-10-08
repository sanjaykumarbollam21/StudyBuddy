import pytest
from app.practice.types import QuestionType, DifficultyLevel, EvaluationVerdict, GeneratedQuestion
from app.practice.generator import QuestionGenerator
from app.practice.evaluator import AnswerEvaluator
from app.practice.service import PracticeService
from app.models.document import DocumentChunk
from app.models.user import User


def test_question_generator_covers_question_types():
    generator = QuestionGenerator()
    questions = generator.generate_questions("Deadlocks & Banker's Algorithm", count=5)

    assert len(questions) == 5
    types_found = {q.question_type for q in questions}
    # Verify MCQ, MULTIPLE_SELECT, TRUE_FALSE, etc. are produced
    assert QuestionType.MCQ in types_found
    assert QuestionType.MULTIPLE_SELECT in types_found
    assert QuestionType.TRUE_FALSE in types_found

    # Verify distractors and explanations exist on MCQs
    mcq = next(q for q in questions if q.question_type == QuestionType.MCQ)
    assert len(mcq.options) >= 3
    assert mcq.correct_answer in mcq.options
    assert len(mcq.distractor_explanations) > 0


def test_question_generator_with_rag_chunks():
    chunks = [
        DocumentChunk(
            id="c-net-1",
            document_id="doc-net",
            user_id="user-1",
            chunk_index=0,
            section_title="OSI Model & Encapsulation",
            content="The transport layer provides end-to-end communication services. TCP ensures reliable byte-stream transmission.",
        )
    ]
    generator = QuestionGenerator()
    questions = generator.generate_questions(
        topic="Computer Networks",
        count=3,
        rag_chunks=chunks,
    )
    assert len(questions) == 3
    rag_q = next((q for q in questions if "OSI Model" in q.prompt), None)
    assert rag_q is not None
    assert rag_q.question_type == QuestionType.MCQ


@pytest.mark.asyncio
async def test_answer_evaluator_mcq_and_misconceptions():
    evaluator = AnswerEvaluator()
    q = GeneratedQuestion(
        id="q-test-1",
        question_type=QuestionType.MCQ,
        prompt="Which condition is NOT required for deadlock?",
        options=["Mutual Exclusion", "Hold and Wait", "Preemption Allowed", "Circular Wait"],
        correct_answer="Preemption Allowed",
        explanation="Preemption allows the OS to take resources away, resolving deadlocks.",
        distractor_explanations={
            "Mutual Exclusion": "Mutual Exclusion is an essential Coffman condition.",
            "Hold and Wait": "Hold and Wait is an essential Coffman condition.",
        },
        concept_tag="coffman_conditions",
    )

    # 1. Correct response
    res_correct = await evaluator.evaluate(q, "Preemption Allowed")
    assert res_correct.is_correct is True
    assert res_correct.score == 1.0
    assert res_correct.verdict == EvaluationVerdict.CORRECT

    # 2. Distractor response with misconception
    res_wrong = await evaluator.evaluate(q, "Mutual Exclusion")
    assert res_wrong.is_correct is False
    assert res_wrong.score == 0.0
    assert res_wrong.verdict == EvaluationVerdict.INCORRECT
    assert "Misconception regarding 'Mutual Exclusion'" in res_wrong.misconception_identified
    assert "Review the core distinction" in res_wrong.remediation_advice


@pytest.mark.asyncio
async def test_answer_evaluator_multiple_select_and_partial_credit():
    evaluator = AnswerEvaluator()
    q = GeneratedQuestion(
        id="q-test-ms",
        question_type=QuestionType.MULTIPLE_SELECT,
        prompt="Select the deadlock prevention strategies:",
        options=["Resource Ordering", "Spooling", "Infinite Wait"],
        correct_answer="Resource Ordering, Spooling",
        explanation="Resource Ordering prevents Circular Wait; Spooling prevents Mutual Exclusion.",
        concept_tag="deadlock_prevention",
    )

    # Full match
    res_full = await evaluator.evaluate(q, "Resource Ordering, Spooling")
    assert res_full.is_correct is True
    assert res_full.score == 1.0

    # Partial match
    res_part = await evaluator.evaluate(q, "Resource Ordering")
    assert res_part.score > 0.0
    assert res_part.verdict == EvaluationVerdict.PARTIALLY_CORRECT


@pytest.mark.asyncio
async def test_practice_service_workflow_and_mastery_tracking(db_session):
    user = User(
        id="user-practice-test-1",
        email="practice_student@example.com",
        full_name="Practice Student",
        hashed_password="hashed_pw_test",
    )
    db_session.add(user)
    await db_session.commit()

    service = PracticeService(db_session)

    # 1. Start a 2-question practice session
    session = await service.start_session(
        user_id=user.id,
        topic="Deadlocks & Banker's Algorithm",
        session_mode="practice",
        count=2,
    )
    assert session["status"] == "in_progress"
    assert session["total_questions"] == 2
    session_id = session["session_id"]
    first_q = session["current_question"]
    assert first_q is not None

    # 2. Submit wrong answer on question 1
    ans_1 = await service.submit_answer(
        user_id=user.id,
        session_id=session_id,
        question_id=first_q["id"],
        student_response="Wrong Answer That Is A Misconception",
    )
    assert ans_1["is_session_completed"] is False
    assert ans_1["current_question_index"] == 1
    assert ans_1["next_question"] is not None
    next_q = ans_1["next_question"]

    # 3. Check that weak areas were logged
    weak_areas = await service.get_weak_areas(user.id)
    assert len(weak_areas) >= 1
    assert "Deadlocks" in weak_areas[0]["topic"]

    # 4. Submit correct answer on question 2
    # Fetch expected answer from DB question to ensure exact match
    ans_2 = await service.submit_answer(
        user_id=user.id,
        session_id=session_id,
        question_id=next_q["id"],
        student_response="True",  # Q2 in deadlock bank is True
    )
    assert ans_2["is_session_completed"] is True
    assert ans_2["next_question"] is None

    # 5. Check practice history
    history = await service.get_practice_history(user.id)
    assert len(history) == 1
    assert history[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_practice_api_endpoints(client, db_session):
    # Signup user
    reg = await client.post(
        "/api/v1/auth/signup",
        json={"email": "api_practice_user@example.com", "password": "Password123!", "full_name": "API Practicer"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start session
    start_res = await client.post(
        "/api/v1/practice/sessions/start",
        json={"topic": "Processes & Synchronization", "count": 2, "session_mode": "practice"},
        headers=headers,
    )
    assert start_res.status_code == 200
    data = start_res.json()
    session_id = data["session_id"]
    q_id = data["current_question"]["id"]

    # 2. Submit answer
    sub_res = await client.post(
        f"/api/v1/practice/sessions/{session_id}/answer",
        json={"question_id": q_id, "student_response": "Progress"},
        headers=headers,
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert "evaluation" in sub_data
    assert "session_score_percentage" in sub_data

    # 3. Fetch history
    hist_res = await client.get("/api/v1/practice/history", headers=headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) == 1

    # 4. Fetch weak areas
    weak_res = await client.get("/api/v1/practice/weak-areas", headers=headers)
    assert weak_res.status_code == 200
    assert isinstance(weak_res.json(), list)
