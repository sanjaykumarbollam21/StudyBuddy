import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.planner.engine import calculate_priority_score, StudyPlannerEngine
from app.agent.decision import AgentDecisionEngine
from app.exam.profiles.registry import ExamProfileRegistry, get_exam_registry
from app.exam.syllabus_service import SyllabusService
from app.exam.pyq_service import PYQService
from app.exam.current_affairs_service import CurrentAffairsService
from app.exam.answer_writing_service import MainsAnswerWritingService
from app.exam.prelims_engine import PrelimsEngine
from app.exam.csat_engine import CSATEngine
from app.exam.adaptive_mock_service import AdaptiveMockService
from app.exam.readiness_dashboard_service import ExamReadinessDashboardService


@pytest.mark.asyncio
async def test_exam_profiles_registry():
    profiles = ExamProfileRegistry.list_all_profiles()
    assert len(profiles) >= 8
    exam_ids = [p["id"] for p in profiles]
    assert "upsc_cse" in exam_ids
    assert "ssc_cgl" in exam_ids
    assert "banking_po" in exam_ids
    assert "gate" in exam_ids or "gate_cs" in exam_ids
    assert "jee_main" in exam_ids or "jee_advanced" in exam_ids
    assert "neet_ug" in exam_ids

    upsc = ExamProfileRegistry.get("upsc_cse")
    assert upsc is not None
    assert upsc.code == "upsc_cse"
    assert len(upsc.stages) >= 2
    assert upsc.default_negative_marking_ratio == 0.33
    assert len(upsc.syllabus_tree) > 0


@pytest.mark.asyncio
async def test_priority_score_formula():
    # Test formula: 0.25*gap + 0.20*exam_weight + 0.20*pyq_freq + 0.15*rev_urgency + 0.10*proximity + 0.05*weakness + 0.05*prereq
    score_high = calculate_priority_score(
        mastery_gap=0.8,
        exam_weight=0.9,
        pyq_frequency=0.8,
        revision_urgency=0.9,
        exam_proximity=0.9,
        weakness_recurrence=0.7,
        prerequisite_importance=0.6,
    )
    score_low = calculate_priority_score(
        mastery_gap=0.1,
        exam_weight=0.2,
        pyq_frequency=0.1,
        revision_urgency=0.1,
        exam_proximity=0.1,
        weakness_recurrence=0.0,
        prerequisite_importance=0.0,
    )
    assert score_high > score_low
    assert 0.0 <= score_high <= 100.0
    assert 0.0 <= score_low <= 100.0


@pytest.mark.asyncio
async def test_competitive_exam_plan_synthesis():
    planner = StudyPlannerEngine()
    plan = await planner.create_competitive_exam_plan(
        user_id="test-student-upsc",
        exam_code="upsc_cse",
        target_year=2027,
        days_until_exam=45,
        daily_study_minutes=360,
    )
    assert plan is not None
    assert plan.subject == "UPSC CSE"
    assert len(plan.schedule_items) > 0
    # Check partition of slots
    slots = [item.session_type for item in plan.schedule_items[:4]]
    assert "learn" in slots
    assert "current_affairs" in slots
    assert "practice" in slots
    assert "revision" in slots


@pytest.mark.asyncio
async def test_agent_competitive_intent_evaluation():
    # 1. Study recommendation intent
    res1 = AgentDecisionEngine.evaluate_competitive_intent("What should I study right now for UPSC?")
    assert res1["intent"] == "study_recommendation"
    assert res1["engine"] == "StudyPlannerEngine"

    # 2. Current affairs intent
    res2 = AgentDecisionEngine.evaluate_competitive_intent("Quiz me on today's current affairs and editorial")
    assert res2["intent"] == "current_affairs"
    assert res2["engine"] == "CurrentAffairsService"

    # 3. Mains answer writing intent
    res3 = AgentDecisionEngine.evaluate_competitive_intent("Please evaluate my mains answer on judicial review")
    assert res3["intent"] == "mains_answer_evaluation"
    assert res3["engine"] == "AnswerWritingService"

    # 4. CSAT intent
    res4 = AgentDecisionEngine.evaluate_competitive_intent("Start a timed CSAT comprehension practice drill")
    assert res4["intent"] == "csat_practice"
    assert res4["engine"] == "CSATEngine"


@pytest.mark.asyncio
async def test_syllabus_service_and_heatmap():
    service = SyllabusService()
    graph = await service.get_or_create_syllabus_graph(exam_id="upsc_cse")
    assert len(graph) > 0
    assert "title" in graph[0]

    heatmap = service.get_topic_heatmap(graph)
    assert "total_topics" in heatmap
    assert heatmap["total_topics"] > 0
    assert "coverage_percentage" in heatmap
    assert "critical" in heatmap


@pytest.mark.asyncio
async def test_pyq_service_filtering_and_scoring():
    service = PYQService()
    pyqs = await service.get_filtered_pyqs(exam_id="upsc_cse", stage="prelims")
    assert len(pyqs) > 0
    first_pyq = pyqs[0]

    # Correct attempt
    correct_attempt = await service.evaluate_attempt(
        user_id="test-student",
        question_id=first_pyq["id"],
        selected_option=first_pyq["correct_answer"],
        time_taken_seconds=30,
    )
    assert correct_attempt["is_correct"] is True
    assert correct_attempt["marks_awarded"] > 0
    assert correct_attempt["error_type"] is None

    # Incorrect attempt with negative penalty
    wrong_opt = "B" if first_pyq["correct_answer"] != "B" else "C"
    wrong_attempt = await service.evaluate_attempt(
        user_id="test-student",
        question_id=first_pyq["id"],
        selected_option=wrong_opt,
        time_taken_seconds=8,  # very fast -> careless_error
    )
    assert wrong_attempt["is_correct"] is False
    assert wrong_attempt["marks_awarded"] < 0
    assert wrong_attempt["error_type"] == "careless_error"


@pytest.mark.asyncio
async def test_current_affairs_and_static_linking():
    ca_service = CurrentAffairsService()
    feed = await ca_service.get_feed(exam_id="upsc_cse", limit=5)
    assert len(feed) > 0

    item = feed[0]
    assert "title" in item
    assert "static_concepts" in item
    assert len(item["static_concepts"]) > 0

    linked = ca_service.link_event_to_static_syllabus(item)
    assert "connected_static_concepts" in linked
    assert len(linked["prospective_prelims_questions"]) > 0
    assert len(linked["prospective_mains_questions"]) > 0


@pytest.mark.asyncio
async def test_mains_answer_writing_rubric_evaluation():
    service = MainsAnswerWritingService()
    question = "Critically analyze the role of Judicial Review in safeguarding constitutionalism in India."
    sample_answer = """
    Judicial Review refers to the power of the judiciary to examine the constitutionality of legislative acts and executive orders. In India, Article 13, Article 32, and Article 226 firmly anchor this doctrine.
    
    Constitutional Safeguards:
    1. Basic Structure Doctrine: Established in Kesavananda Bharati (1973), ensuring that amending power under Article 368 is not unlimited.
    2. Protection of Fundamental Rights: For example, in the Puttaswamy case (2017), the Supreme Court upheld the Right to Privacy.
    
    Contemporary Challenges:
    However, concerns regarding judicial overreach have emerged when courts enter executive policymaking. This can disrupt separation of powers under Article 50.
    
    Way Forward:
    In conclusion, judicial review is indispensable for checks and balances. A harmonious balance between judicial restraint and constitutional vigilance is the need of the hour.
    """
    evaluation = service.evaluate_answer(
        question_text=question,
        student_answer=sample_answer,
        total_marks=10.0,
        word_limit=150,
        paper_name="General Studies Paper II",
    )
    assert evaluation["word_count"] > 50
    assert evaluation["marks_obtained"] > 5.0
    assert "rubric_breakdown" in evaluation
    assert "content_accuracy" in evaluation["rubric_breakdown"]
    assert "structural_flow" in evaluation["rubric_breakdown"]
    assert "model_outline" in evaluation
    assert len(evaluation["strengths"]) > 0


@pytest.mark.asyncio
async def test_prelims_engine_mcq_types_and_elimination():
    engine = PrelimsEngine()
    q = engine.generate_practice_question(
        exam_id="upsc_cse",
        subject="Indian Polity",
        topic="Parliamentary System",
        question_type="statement_based",
    )
    assert q["question_type"] == "statement_based"
    assert len(q["options"]) == 4

    # Test extreme qualifier detection
    extreme_stmt = "The Governor can always unilaterally dismiss the council of ministers under all circumstances."
    balanced_stmt = "The Governor generally acts on the aid and advice of the Council of Ministers."
    assert engine.detect_extreme_qualifiers(extreme_stmt) is True
    assert engine.detect_extreme_qualifiers(balanced_stmt) is False


@pytest.mark.asyncio
async def test_csat_engine_timed_session():
    session = CSATEngine.generate_practice_session(difficulty="medium", count=5)
    assert "session_id" in session
    assert len(session["questions"]) == 5
    assert session["negative_marking_penalty"] == 0.83
    assert session["time_limit_minutes"] > 0


@pytest.mark.asyncio
async def test_adaptive_mock_service():
    mock_service = AdaptiveMockService()
    mock_test = mock_service.generate_adaptive_mock(
        exam_id="upsc_cse",
        stage="prelims",
        paper_name="General Studies Paper I",
        question_count=10,
    )
    assert mock_test["total_questions"] == 10
    assert mock_test["total_marks"] == 20.0
    assert len(mock_test["questions"]) == 10


@pytest.mark.asyncio
async def test_readiness_dashboard_service():
    readiness_service = ExamReadinessDashboardService()
    report = await readiness_service.get_dashboard_metrics(
        user_id="test-student-readiness",
        exam_id="upsc_cse",
    )
    assert "readiness_radar" in report
    radar = report["readiness_radar"]
    assert "overall_readiness" in radar
    assert "concept_readiness" in radar
    assert "prelims_readiness" in radar
    assert "mains_readiness" in radar
    assert "revision_readiness" in radar
    assert "mock_readiness" in radar
    assert "topic_heatmap" in report


@pytest.mark.asyncio
async def test_competitive_exam_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Profiles list
        resp = await client.get("/api/v1/competitive-exams/profiles")
        assert resp.status_code == 200
        profiles = resp.json()
        assert len(profiles) >= 8

        # 2. PYQs list
        resp = await client.get("/api/v1/competitive-exams/pyqs?exam_id=upsc_cse&stage=prelims")
        assert resp.status_code == 200
        pyqs = resp.json()
        assert len(pyqs) > 0

        # 3. Current affairs feed
        resp = await client.get("/api/v1/competitive-exams/current-affairs?exam_id=upsc_cse")
        assert resp.status_code == 200
        ca = resp.json()
        assert len(ca) > 0

        # 4. CSAT session
        resp = await client.get("/api/v1/competitive-exams/csat/session?question_count=5")
        assert resp.status_code == 200
        csat = resp.json()
        assert len(csat["questions"]) == 5

        # 5. Answer writing evaluation
        resp = await client.post(
            "/api/v1/competitive-exams/answer-writing/evaluate",
            json={
                "question_text": "Examine the role of the Election Commission in ensuring free and fair elections.",
                "student_answer_text": "The Election Commission of India (Article 324) is a permanent constitutional body tasked with conducting free and fair elections. For example, the Model Code of Conduct ensures a level playing field. However, regulation of social media and hate speech remain bottlenecks. In conclusion, statutory backing for MCC will strengthen electoral democracy.",
                "paper_id": "General Studies Paper II",
                "word_limit": 150,
                "allocated_marks": 10.0,
            },
        )
        assert resp.status_code == 200
        eval_res = resp.json()
        assert "marks_obtained" in eval_res
        assert "rubric_breakdown" in eval_res
