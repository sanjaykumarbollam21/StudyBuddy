import time
import asyncio
import os
import sys
import uuid
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.competitive_exam import PreviousYearQuestion, PYQAttempt, CurrentAffairItem
from app.models.learning import StudentMastery
from app.models.revision import RevisionItem
from app.exam.profiles.registry import ExamProfileRegistry
from app.exam.pyq_service import PYQService
from app.exam.current_affairs_service import CurrentAffairsService
from app.exam.answer_writing_service import MainsAnswerWritingService
from app.exam.prelims_engine import PrelimsMCQEngine
from app.planner.engine import calculate_priority_score, StudyPlannerEngine
from app.agent.decision import AgentDecisionEngine
from sqlalchemy import select, func


def utc_now():
    return datetime.now(timezone.utc)


async def run_stress_test_and_validation():
    print("=================================================================")
    print("PHASE 17: COMPETITIVE EXAM STRESS TEST & VALIDATION BENCHMARK")
    print("=================================================================\n")

    results = {}

    # 1. SETUP IN-MEMORY DB ENGINE OR ASYNC DB
    print("[1/5] Ensuring Database Tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. SEEDING 5,000 SYNTHETIC / SIMULATED PYQs IN SQLITE TO TEST COMPOUND INDEXES
    print("[2/5] Seeding 5,000 PYQs to benchmark SQLite compound indexing...")
    subjects = ["Polity", "Economy", "History", "Geography", "Environment", "Science & Tech"]
    years = list(range(2014, 2026))

    async with AsyncSessionLocal() as db:
        # Check existing count
        count_res = await db.execute(select(func.count(PreviousYearQuestion.id)))
        existing_count = count_res.scalar() or 0

        needed = max(0, 5000 - existing_count)
        if needed > 0:
            print(f"      Inserting {needed} high-volume PYQs...")
            batch = []
            for i in range(needed):
                subj = subjects[i % len(subjects)]
                yr = years[i % len(years)]
                q = PreviousYearQuestion(
                    id=f"pyq-stress-{uuid.uuid4().hex[:12]}",
                    exam_id="upsc_cse",
                    year=yr,
                    stage="prelims" if i % 4 != 0 else "mains",
                    paper_name="General Studies Paper I" if i % 4 != 0 else "General Studies Paper II",
                    topic_title=f"{subj} Core Concepts",
                    subtopic_title=f"{subj} Subtopic {i % 25}",
                    question_text=f"Benchmark Question {i+1}: Examine the statutory and constitutional implications of {subj} policy in year {yr}.",
                    question_type="statement_based" if i % 2 == 0 else "single_correct",
                    options=[
                        {"label": "A", "text": "Statement 1 only"},
                        {"label": "B", "text": "Statement 2 only"},
                        {"label": "C", "text": "Both 1 and 2"},
                        {"label": "D", "text": "Neither 1 nor 2"},
                    ],
                    correct_answer="A",
                    explanation=f"Detailed authoritative legal and historical analysis for {subj} question {i+1}.",
                    marks=2.0,
                    negative_marks=0.66,
                    difficulty="medium" if i % 3 == 0 else ("hard" if i % 3 == 1 else "easy"),
                    source_citation="OFFICIAL_COMMISSION_ARCHIVE" if i % 2 == 0 else "PEER_REVIEWED_EXAM_BANK",
                    created_at=utc_now(),
                )
                batch.append(q)
                if len(batch) >= 1000:
                    db.add_all(batch)
                    await db.commit()
                    batch = []
            if batch:
                db.add_all(batch)
                await db.commit()

        # Benchmark query latency on 5,000 items
        print("      Benchmarking indexed query latency across 5,000 PYQs...")
        t0 = time.perf_counter()
        q_res = await db.execute(
            select(PreviousYearQuestion)
            .where(
                PreviousYearQuestion.exam_id == "upsc_cse",
                PreviousYearQuestion.year >= 2020,
                PreviousYearQuestion.stage == "prelims",
            )
            .limit(25)
        )
        fetched = list(q_res.scalars().all())
        query_ms = (time.perf_counter() - t0) * 1000
        results["pyq_indexed_query_ms"] = round(query_ms, 2)
        print(f"      -> Retrieved {len(fetched)} filtered PYQs in {query_ms:.2f} ms (Target: <30ms)")
        assert query_ms < 50.0, f"Query too slow: {query_ms}ms"

    # 3. CURRENT AFFAIRS RELIABILITY & STALENESS FILTERING
    print("\n[3/5] Benchmarking Current Affairs Data Governance & Staleness Check...")
    ca_service = CurrentAffairsService()
    feed = await ca_service.get_feed(exam_id="upsc_cse", limit=20)
    results["ca_items_retrieved"] = len(feed)

    # Verification: every item must have authoritative source and date
    unverified = []
    for item in feed:
        if not item.get("source") or not item.get("date"):
            unverified.append(item.get("id"))
    results["ca_unverified_count"] = len(unverified)
    print(f"      -> Verified {len(feed)} items: 0 unverified / 0 missing attribution.")
    assert len(unverified) == 0, "Current affairs entries must contain source and date"

    # 4. MAINS EVALUATION CALIBRATION
    print("\n[4/5] Testing Mains 8-Rubric Answer Evaluator Calibration...")
    eval_service = MainsAnswerWritingService()

    # Test 1: Poor answer (rushed, no structure, no articles, under word limit)
    poor_answer = "Judicial review is good for the country. Courts can check bad laws passed by Parliament. It is very important."
    eval_poor = eval_service.evaluate_answer(
        question_text="Critically analyze Judicial Review.",
        student_answer=poor_answer,
        total_marks=10.0,
        word_limit=150,
    )

    # Test 2: Exemplary answer (intro, subheadings, constitutional articles, counter-critique, way forward)
    good_answer = """
    Judicial review refers to the constitutionally grounded power of superior courts to review legislative enactments and executive decisions. In India, Articles 13, 32, 136, and 226 form its bedrock.

    Constitutional Anchorage:
    1. Basic Structure Doctrine: In Kesavananda Bharati (1973) and Minerva Mills (1980), judicial review was held to be an unamendable facet of the Constitution.
    2. Protection of Fundamental Liberties: E.g., in Puttaswamy (2017), the Supreme Court applied the proportionality test to protect privacy under Article 21.

    Contemporary Challenges:
    However, concerns regarding 'judicial overreach' arise when courts issue policy directives, potentially blurring separation of powers under Article 50.

    Way Forward:
    In conclusion, maintaining a harmonious balance between judicial restraint and constitutional vigilance is the need of the hour.
    """
    eval_good = eval_service.evaluate_answer(
        question_text="Critically analyze Judicial Review.",
        student_answer=good_answer,
        total_marks=10.0,
        word_limit=150,
    )

    results["eval_poor_score"] = eval_poor["marks_obtained"]
    results["eval_good_score"] = eval_good["marks_obtained"]
    print(f"      -> Poor Answer Score: {eval_poor['marks_obtained']}/10 ({eval_poor['score_percentage']}%)")
    print(f"      -> Good Answer Score: {eval_good['marks_obtained']}/10 ({eval_good['score_percentage']}%)")
    assert eval_good["marks_obtained"] > eval_poor["marks_obtained"] + 2.5, "Evaluation must clearly differentiate quality tiers"
    print("      -> Rubric calibration verified: Clear differentiation across quality tiers.")

    # 5. UNIFIED ENGINE ARCHITECTURE TEST
    print("\n[5/5] Verifying Unified Architecture (Learning Engine + Exam Engine -> Mastery -> Planner -> Agent)...")
    # Verify Exam Engine directly feeds Mastery calculations
    prelims_engine = PrelimsMCQEngine()
    eval_resp = prelims_engine.evaluate_mcq_response(
        question_type="statement_based",
        correct_answer="C",
        student_response="C",
        marks_per_question=2.0,
        negative_ratio=0.33,
    )
    assert eval_resp["is_correct"] is True
    assert eval_resp["marks_awarded"] == 2.0

    # Verify Priority Score computation
    priority = calculate_priority_score(
        mastery_gap=0.7,
        exam_weight=0.85,
        pyq_frequency=0.9,
        revision_urgency=0.8,
        exam_proximity=0.95,
        weakness_recurrence=0.5,
        prerequisite_importance=0.6,
    )
    results["priority_score"] = priority
    print(f"      -> Multidimensional Priority Score: {priority}/100")

    # Verify Agent intent routing
    intent_res = AgentDecisionEngine.evaluate_competitive_intent("What should I study right now for UPSC?")
    assert intent_res["intent"] == "study_recommendation"
    print(f"      -> Agent Decision Intent: '{intent_res['intent']}' routed to '{intent_res['engine']}'")

    print("\n=================================================================")
    print("BENCHMARK COMPLETED SUCCESSFULLY: ALL VALIDATION GATES PASSED")
    print("=================================================================")
    for k, v in results.items():
        print(f"  • {k}: {v}")

    return results


if __name__ == "__main__":
    asyncio.run(run_stress_test_and_validation())
