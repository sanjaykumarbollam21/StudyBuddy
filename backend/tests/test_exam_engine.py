import pytest
from datetime import datetime, timezone, timedelta
from app.exam.generator import ExamGenerator, DEFAULT_BLUEPRINTS
from app.exam.readiness import ReadinessEngine
from app.exam.service import ExamService
from app.models.exam import MockExamSession, ExamConfig


def test_blueprint_and_exam_generation():
    generator = ExamGenerator()
    bp = generator.get_default_blueprint("Operating Systems")

    assert "Processes" in bp
    assert "Deadlocks" in bp
    assert "CPU Scheduling" in bp
    assert "Memory Management" in bp

    # Generate 10 questions for 100 marks with 0.25 negative marking
    questions = generator.generate_exam_questions(
        subject="Operating Systems",
        blueprint=bp,
        total_questions=10,
        total_marks=100.0,
        negative_marking_ratio=0.25,
    )

    assert len(questions) == 10
    total_marks_sum = sum(q["marks"] for q in questions)
    assert total_marks_sum == 100.0

    # Verify each question has marks, negative penalty, and order_index
    for idx, q in enumerate(questions):
        assert q["marks"] == 10.0
        assert q["negative_marks"] == 2.5
        assert q["order_index"] == idx + 1
        assert "prompt" in q
        assert "correct_answer" in q
        assert "topic" in q

    # Check topic representation adheres to blueprint
    topics_in_exam = {q["topic"] for q in questions}
    assert len(topics_in_exam) >= 4


def test_mock_exam_scoring_and_negative_marking():
    service = ExamService()
    generator = ExamGenerator()
    questions = generator.generate_exam_questions(
        subject="Operating Systems",
        total_questions=4,
        total_marks=40.0,
        negative_marking_ratio=0.25,
    )

    # Question 0: Answered correctly -> +10 marks
    # Question 1: Answered incorrectly -> -2.5 marks
    # Question 2: Left blank (unanswered) -> 0 marks, 0 penalty
    # Question 3: Answered correctly -> +10 marks
    q0_ans = questions[0]["correct_answer"]
    q1_ans = "Completely Incorrect Distractor"
    q2_ans = ""  # blank
    q3_ans = questions[3]["correct_answer"]

    answers = {
        questions[0]["id"]: {"response": q0_ans},
        questions[1]["id"]: {"response": q1_ans},
        questions[2]["id"]: {"response": q2_ans},
        questions[3]["id"]: {"response": q3_ans},
    }

    dummy_session = MockExamSession(
        id="session-test-scoring",
        user_id="user-test-1",
        title="Test Scoring Exam",
        subject="Operating Systems",
        duration_minutes=30,
        total_questions=4,
        total_marks=40.0,
        questions_data=questions,
        answers_record=answers,
        detailed_analysis={},
    )

    import asyncio
    evaluated_session = asyncio.run(
        service.submit_mock_exam(
            user_id="user-test-1",
            session_id="session-test-scoring",
            answers=answers,
            in_memory_session=dummy_session,
        )
    )

    assert evaluated_session.status == "submitted"
    # Net marks = 10 - 2.5 + 0 + 10 = 17.5
    assert evaluated_session.marks_obtained == 17.5
    assert evaluated_session.negative_marks_deducted == 2.5
    # Score % = 17.5 / 40.0 * 100 = 43.8%
    assert evaluated_session.score_percentage == 43.8

    analysis = evaluated_session.detailed_analysis
    assert analysis["correct_count"] == 2
    assert analysis["incorrect_count"] == 1
    assert analysis["unanswered_count"] == 1


def test_post_exam_topic_analysis_and_cognitive_diagnosis():
    service = ExamService()
    generator = ExamGenerator()
    questions = generator.generate_exam_questions(
        subject="Operating Systems",
        total_questions=6,
        total_marks=60.0,
        negative_marking_ratio=0.25,
    )

    # Force a deadlock distractor error
    answers = {}
    for q in questions:
        if "deadlock" in q.get("topic", "").lower():
            # Deliberately pick an avoidance distractor for a prevention question
            distractors = list(q.get("distractor_explanations", {}).keys())
            answers[q["id"]] = {"response": distractors[0] if distractors else "Wrong"}
        else:
            answers[q["id"]] = {"response": q["correct_answer"]}

    dummy_session = MockExamSession(
        id="session-test-diag",
        user_id="user-test-2",
        title="Test Diagnostic Exam",
        subject="Operating Systems",
        duration_minutes=45,
        total_questions=6,
        total_marks=60.0,
        questions_data=questions,
        answers_record=answers,
        detailed_analysis={},
    )

    import asyncio
    result = asyncio.run(
        service.submit_mock_exam(
            user_id="user-test-2",
            session_id="session-test-diag",
            answers=answers,
            in_memory_session=dummy_session,
        )
    )

    da = result.detailed_analysis
    cog_diag = da["cognitive_diagnosis"]

    # Verify diagnostic specifically pinpoints deadlock confusion
    assert "deadlock" in cog_diag["core_issue"].lower()
    assert "prevention" in cog_diag["deep_explanation"].lower()
    assert "avoidance" in cog_diag["deep_explanation"].lower()

    # Verify closed-loop remediation CTA target
    remediation = da["remediation_action"]
    assert "Deadlock" in remediation["target_topic"]
    assert "Reteach" in remediation["cta_title"]
    assert "prompt" in remediation

    # Verify topic analysis tier categorization
    topics = da["topic_analysis"]
    tiers = {t["tier"] for t in topics}
    assert any(tier in tiers for tier in ["Strong", "Good", "Weak", "Critical"])


def test_multi_factor_readiness_calculation():
    engine = ReadinessEngine()
    blueprint = {
        "Processes": 0.20,
        "CPU Scheduling": 0.20,
        "Synchronization": 0.20,
        "Deadlocks": 0.20,
        "Memory Management": 0.20,
    }

    # Student is strong in CPU Scheduling & Processes, but weak in Synchronization and critical in Deadlocks
    masteries = {
        "Processes": 76.0,
        "CPU Scheduling": 89.0,
        "Synchronization": 48.0,
        "Deadlocks": 31.0,
        "Memory Management": 65.0,
    }

    recall_stats = {"total_items": 10, "due_items": 3}
    practice_stats = {"average_accuracy": 70.0}
    mock_stats = {"latest_score": 74.0, "unanswered_ratio": 0.1}

    result = engine.compute_exam_readiness(
        blueprint=blueprint,
        topic_masteries=masteries,
        recall_stats=recall_stats,
        practice_stats=practice_stats,
        mock_stats=mock_stats,
    )

    # Overall readiness should reflect multi-factor calculation
    assert 55.0 <= result["readiness_percentage"] <= 80.0
    assert "ready for this exam" in result["readiness_message"]

    # Actionable projection should call out Synchronization and Deadlocks
    projection = result["actionable_projection"]
    assert "Synchronization" in projection or "Deadlocks" in projection
    assert "sessions" in projection

    # Dimension scores breakdown
    dims = result["dimension_scores"]
    assert "knowledge_coverage" in dims
    assert "concept_mastery" in dims
    assert "recent_recall" in dims
    assert "practice_accuracy" in dims
    assert "mock_test_performance" in dims
    assert "time_management" in dims
    assert "weak_penalty_applied" in dims
