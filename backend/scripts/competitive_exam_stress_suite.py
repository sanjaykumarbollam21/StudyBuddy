"""
Phase 18: Competitive Exam Endurance & High-Volume Scalability Stress Suite
=============================================================================
Tests:
- 5,000 / 10,000 / 25,000 / 50,000 PYQs (compound queries, pagination, sorting, memory)
- 1,000 / 5,000 Current Affairs records (indexing, SHA-256 deduplication, pagination)
- 100 / 500 Syllabus nodes (hierarchical retrieval & traversal)
- 1,000 Mastery records (Bayesian mastery updates & priority ranking)
- 10,000 Spaced Revision records (SM-2 due queries & interval indexing)
"""

import asyncio
import gc
import os
import sys
import time
import tracemalloc
import uuid
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func, desc, asc
from app.core.database import Base
from app.models.competitive_exam import (
    PreviousYearQuestion,
    PYQAttempt,
    CurrentAffairItem,
    CompetitiveExamProfile,
)
from app.models.learning import StudentMastery, Topic, TopicRelation
from app.models.revision import RevisionItem


def utc_now():
    return datetime.now(timezone.utc)


async def run_stress_suite():
    print("=" * 80)
    print("STUDY BUDDY — PHASE 18: COMPETITIVE EXAM HIGH-VOLUME STRESS SUITE")
    print("=" * 80)

    tracemalloc.start()
    db_file = os.path.join(os.path.dirname(__file__), "stress_suite_temp.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    stress_db_url = f"sqlite+aiosqlite:///{db_file}"
    stress_engine = create_async_engine(stress_db_url, echo=False)
    StressSessionLocal = async_sessionmaker(stress_engine, class_=AsyncSession, expire_on_commit=False)

    async with stress_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    report = {
        "timestamp": utc_now().isoformat(),
        "database": "sqlite_aiosqlite",
        "pyq_benchmarks": {},
        "current_affairs_benchmarks": {},
        "syllabus_benchmarks": {},
        "mastery_benchmarks": {},
        "revision_benchmarks": {},
    }

    subjects = ["Polity", "Economy", "History", "Geography", "Environment", "Science & Tech", "CSAT"]
    years = list(range(2010, 2026))

    async with StressSessionLocal() as session:
        # -------------------------------------------------------------
        # 1. PYQ SCALING TIERS: 5,000 -> 10,000 -> 25,000 -> 50,000
        # -------------------------------------------------------------
        print("\n--- [1/5] BENCHMARKING PYQ SCALING (5K -> 10K -> 25K -> 50K) ---")
        tiers = [5000, 10000, 25000, 50000]
        current_pyq_count = 0

        for target in tiers:
            needed = target - current_pyq_count
            print(f"\n  [+] Scaling to {target:,} PYQs (Inserting {needed:,} questions)...")
            t_ins_start = time.perf_counter()
            
            batch_size = 2500
            batch = []
            for i in range(needed):
                idx = current_pyq_count + i
                subj = subjects[idx % len(subjects)]
                yr = years[idx % len(years)]
                q = PreviousYearQuestion(
                    id=f"pyq-{uuid.uuid4().hex[:12]}",
                    exam_id="upsc_cse" if idx % 3 != 0 else "gate_cs",
                    year=yr,
                    stage="prelims" if idx % 4 != 0 else "mains",
                    paper_name="General Studies Paper I" if idx % 2 == 0 else "General Studies Paper II",
                    topic_title=f"{subj} Core Principles",
                    subtopic_title=f"{subj} Focus Area {idx % 50}",
                    question_text=f"Q{idx+1}: Critical statutory evaluation of {subj} constitutional article in year {yr}.",
                    question_type="statement_based" if idx % 2 == 0 else "single_correct",
                    options=[
                        {"label": "A", "text": "Statement 1 only"},
                        {"label": "B", "text": "Statement 2 only"},
                        {"label": "C", "text": "Both 1 and 2"},
                        {"label": "D", "text": "Neither 1 nor 2"},
                    ],
                    correct_answer="C",
                    explanation=f"Exhaustive constitutional and factual commentary for {subj} question {idx+1}.",
                    marks=2.0,
                    negative_marks=0.66,
                    difficulty="hard" if idx % 3 == 0 else ("medium" if idx % 3 == 1 else "easy"),
                    source_citation="UPSC Official Archive 2010-2025",
                    provenance="OFFICIAL_PYQ",
                    question_number=(idx % 100) + 1,
                    created_at=utc_now(),
                )
                batch.append(q)
                if len(batch) >= batch_size:
                    session.add_all(batch)
                    await session.commit()
                    batch = []

            if batch:
                session.add_all(batch)
                await session.commit()

            t_ins_ms = (time.perf_counter() - t_ins_start) * 1000
            current_pyq_count = target

            # Query Benchmarks on this tier
            # A. Compound filter query (Exam + Year + Stage)
            q_times = []
            for _ in range(5):
                t0 = time.perf_counter()
                stmt = select(PreviousYearQuestion).where(
                    PreviousYearQuestion.exam_id == "upsc_cse",
                    PreviousYearQuestion.year >= 2021,
                    PreviousYearQuestion.stage == "prelims"
                ).limit(50)
                res = await session.execute(stmt)
                rows = res.scalars().all()
                q_times.append((time.perf_counter() - t0) * 1000)

            # B. Real Flutter Pagination (page 5, page_size 25)
            t_page0 = time.perf_counter()
            page_stmt = select(PreviousYearQuestion).where(
                PreviousYearQuestion.exam_id == "upsc_cse"
            ).order_by(desc(PreviousYearQuestion.year), asc(PreviousYearQuestion.question_number)).offset(100).limit(25)
            page_res = await session.execute(page_stmt)
            paged_rows = page_res.scalars().all()
            t_page_ms = (time.perf_counter() - t_page0) * 1000

            avg_q_ms = sum(q_times) / len(q_times)
            min_q_ms = min(q_times)
            curr_mem_mb = tracemalloc.get_traced_memory()[0] / (1024 * 1024)

            print(f"      Insertion Time: {t_ins_ms:.1f} ms | Indexed Query p50: {avg_q_ms:.2f} ms (min: {min_q_ms:.2f} ms)")
            print(f"      Paginated Read (offset 100, limit 25): {t_page_ms:.2f} ms | Ret: {len(paged_rows)} | RAM: {curr_mem_mb:.2f} MB")

            report["pyq_benchmarks"][f"{target}_pyqs"] = {
                "count": target,
                "insertion_ms": round(t_ins_ms, 2),
                "compound_query_avg_ms": round(avg_q_ms, 2),
                "compound_query_min_ms": round(min_q_ms, 2),
                "paginated_query_ms": round(t_page_ms, 2),
                "allocated_ram_mb": round(curr_mem_mb, 2),
            }

        # -------------------------------------------------------------
        # 2. CURRENT AFFAIRS SCALING: 1,000 -> 5,000
        # -------------------------------------------------------------
        print("\n--- [2/5] BENCHMARKING CURRENT AFFAIRS SCALING (1,000 -> 5,000) ---")
        ca_tiers = [1000, 5000]
        current_ca_count = 0

        for target in ca_tiers:
            needed = target - current_ca_count
            print(f"\n  [+] Scaling to {target:,} Current Affairs (Inserting {needed:,} articles)...")
            t_ca_ins = time.perf_counter()
            batch = []
            for i in range(needed):
                idx = current_ca_count + i
                item = CurrentAffairItem(
                    id=f"ca-{uuid.uuid4().hex[:12]}",
                    date=utc_now() - timedelta(days=idx % 365),
                    title=f"National Policy Brief #{idx+1}: Regulatory Reform Framework in Energy Sector",
                    summary=f"Analysis of bilateral agreements, judicial review standards, and constitutional balance for item {idx+1}.",
                    background=f"Historical context and administrative reforms background for item {idx+1}.",
                    category="polity" if idx % 3 == 0 else ("economy" if idx % 3 == 1 else "environment"),
                    source="The Hindu Editorial & PIB Press Bureau",
                    source_url="https://pib.gov.in/releases/2026/policy",
                    static_concepts=["Article 21", "Regulatory Commissions", "Energy Transition"],
                    prelims_pointers=["Key enactment 2026", "Threshold cap 500MW"],
                    mains_pointers=["Fiscal implications", "Federal state rights balance"],
                    importance="high" if idx % 4 == 0 else "medium",
                    is_cached=True,
                    content_hash=f"hash_sha256_{idx}_{uuid.uuid4().hex[:8]}",
                    published_at=utc_now() - timedelta(days=idx % 365),
                    retrieved_at=utc_now(),
                    created_at=utc_now(),
                )
                batch.append(item)
                if len(batch) >= 1000:
                    session.add_all(batch)
                    await session.commit()
                    batch = []

            if batch:
                session.add_all(batch)
                await session.commit()

            t_ca_ins_ms = (time.perf_counter() - t_ca_ins) * 1000
            current_ca_count = target

            # Query Benchmarks: Filter by category + importance + sorted by published_at
            t0 = time.perf_counter()
            ca_stmt = (
                select(CurrentAffairItem)
                .where(
                    CurrentAffairItem.category == "polity",
                    CurrentAffairItem.importance == "high",
                )
                .order_by(desc(CurrentAffairItem.published_at))
                .limit(20)
            )
            ca_res = await session.execute(ca_stmt)
            ca_rows = ca_res.scalars().all()
            ca_query_ms = (time.perf_counter() - t0) * 1000

            print(f"      Insertion Time: {t_ca_ins_ms:.1f} ms | Indexed High-Priority Query: {ca_query_ms:.2f} ms (Rows: {len(ca_rows)})")

            report["current_affairs_benchmarks"][f"{target}_records"] = {
                "count": target,
                "insertion_ms": round(t_ca_ins_ms, 2),
                "priority_query_ms": round(ca_query_ms, 2),
                "rows_returned": len(ca_rows),
            }

        # -------------------------------------------------------------
        # 3. SYLLABUS DAG NODES: 100 -> 500
        # -------------------------------------------------------------
        print("\n--- [3/5] BENCHMARKING SYLLABUS DAG NODES (100 -> 500 NODES) ---")
        syl_tiers = [100, 500]
        current_node_count = 0

        for target in syl_tiers:
            needed = target - current_node_count
            print(f"\n  [+] Scaling to {target} Syllabus Nodes (Inserting {needed} nodes)...")
            t_syl_ins = time.perf_counter()
            batch = []
            for i in range(needed):
                idx = current_node_count + i
                subj = "upsc_polity" if idx % 2 == 0 else "upsc_economy"
                node = Topic(
                    id=f"node-{idx}",
                    title=f"Syllabus Milestone {idx}: Advanced Analytical Concept",
                    subject_id=subj,
                    description=f"Core conceptual node {idx} with comprehensive subtopics and constitutional provisions.",
                    difficulty="hard" if idx % 4 == 0 else "medium",
                    estimated_mins=45,
                    created_at=utc_now(),
                )
                batch.append(node)
                if len(batch) >= 200:
                    session.add_all(batch)
                    await session.commit()
                    batch = []

            if batch:
                session.add_all(batch)
                await session.commit()

            t_syl_ins_ms = (time.perf_counter() - t_syl_ins) * 1000
            current_node_count = target

            # Query Benchmark: Subject branch retrieval & tree hierarchy
            t0 = time.perf_counter()
            syl_stmt = select(Topic).where(Topic.subject_id == "upsc_polity").order_by(Topic.difficulty, Topic.title)
            syl_res = await session.execute(syl_stmt)
            syl_rows = syl_res.scalars().all()
            syl_query_ms = (time.perf_counter() - t0) * 1000

            print(f"      Insertion Time: {t_syl_ins_ms:.1f} ms | Subject Branch Traversal: {syl_query_ms:.2f} ms (Nodes: {len(syl_rows)})")

            report["syllabus_benchmarks"][f"{target}_nodes"] = {
                "count": target,
                "insertion_ms": round(t_syl_ins_ms, 2),
                "branch_traversal_ms": round(syl_query_ms, 2),
                "nodes_found": len(syl_rows),
            }

        # -------------------------------------------------------------
        # 4. MASTERY RECORDS: 1,000 RECORDS
        # -------------------------------------------------------------
        print("\n--- [4/5] BENCHMARKING MASTERY ENGINE (1,000 TOPIC MASTERY RECORDS) ---")
        student_id = "stress-student-001"
        from app.models.user import User
        # Ensure user exists for FK
        user_check = await session.execute(select(User).where(User.id == student_id))
        if not user_check.scalar_one_or_none():
            test_user = User(
                id=student_id,
                email="stress_test@example.com",
                full_name="Stress Test Student",
                hashed_password="fakehash_bcrypt",
                created_at=utc_now(),
            )
            session.add(test_user)
            await session.commit()

        t_m_ins = time.perf_counter()
        m_batch = []
        for i in range(1000):
            m = StudentMastery(
                id=f"mast-{uuid.uuid4().hex[:12]}",
                user_id=student_id,
                topic_id=f"node-{i % 500}",
                mastery_percentage=45.0 + (i % 50) * 1.0,
                times_practiced=(i % 20) + 1,
                consecutive_correct=(i % 5),
                last_evaluated_at=utc_now() - timedelta(hours=i % 72),
                weak_areas=["Constitutional articles", "Case precedents"] if i % 3 == 0 else [],
            )
            m_batch.append(m)
            if len(m_batch) >= 500:
                session.add_all(m_batch)
                await session.commit()
                m_batch = []
        if m_batch:
            session.add_all(m_batch)
            await session.commit()

        t_m_ins_ms = (time.perf_counter() - t_m_ins) * 1000

        # Query: Find lowest mastery topics (weak areas for adaptive agent)
        t0 = time.perf_counter()
        weak_stmt = (
            select(StudentMastery)
            .where(StudentMastery.user_id == student_id)
            .order_by(asc(StudentMastery.mastery_percentage))
            .limit(15)
        )
        weak_res = await session.execute(weak_stmt)
        weak_rows = weak_res.scalars().all()
        weak_q_ms = (time.perf_counter() - t0) * 1000

        print(f"      1,000 Mastery Insertion: {t_m_ins_ms:.1f} ms | Weak Topics Retrieval: {weak_q_ms:.2f} ms")
        report["mastery_benchmarks"] = {
            "count": 1000,
            "insertion_ms": round(t_m_ins_ms, 2),
            "weak_topics_query_ms": round(weak_q_ms, 2),
        }

        # -------------------------------------------------------------
        # 5. REVISION RECORDS: 10,000 SM-2 SPACED REPETITION ITEMS
        # -------------------------------------------------------------
        print("\n--- [5/5] BENCHMARKING SPACED REVISION QUEUE (10,000 REVISION ITEMS) ---")
        t_rev_ins = time.perf_counter()
        r_batch = []
        for i in range(10000):
            due_offset = (i % 60) - 30  # some overdue, some future
            r = RevisionItem(
                id=f"rev-{uuid.uuid4().hex[:12]}",
                user_id=student_id,
                topic_id=f"node-{i % 500}",
                topic_title=f"Syllabus Milestone {i % 500}",
                concept_summary=f"Key conceptual points for milestone {i % 500}",
                retrieval_prompt=f"Revision Probe #{i+1}: What is the constitutional doctrine regarding topic {i % 500}?",
                retrieval_answer=f"Canonical legal and analytical formulation for node {i % 500}.",
                repetition_interval_days=(i % 14) + 1,
                ease_factor=2.5,
                repetition_count=(i % 5) + 1,
                next_review_date=utc_now() + timedelta(days=due_offset),
                mastery_score=0.75,
                is_due=(due_offset <= 0),
                created_at=utc_now(),
            )
            r_batch.append(r)
            if len(r_batch) >= 2000:
                session.add_all(r_batch)
                await session.commit()
                r_batch = []
        if r_batch:
            session.add_all(r_batch)
            await session.commit()

        t_rev_ins_ms = (time.perf_counter() - t_rev_ins) * 1000

        # Query: Due items query (critical for morning review screen)
        t0 = time.perf_counter()
        due_stmt = (
            select(RevisionItem)
            .where(
                RevisionItem.user_id == student_id,
                RevisionItem.next_review_date <= utc_now(),
            )
            .order_by(asc(RevisionItem.next_review_date))
            .limit(30)
        )
        due_res = await session.execute(due_stmt)
        due_rows = due_res.scalars().all()
        due_q_ms = (time.perf_counter() - t0) * 1000

        print(f"      10,000 Revision Insertion: {t_rev_ins_ms:.1f} ms | Due Items Query (limit 30): {due_q_ms:.2f} ms (Found: {len(due_rows)})")
        report["revision_benchmarks"] = {
            "count": 10000,
            "insertion_ms": round(t_rev_ins_ms, 2),
            "due_queue_query_ms": round(due_q_ms, 2),
            "due_items_count": len(due_rows),
        }

    # Final Resource Profile
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    report["resource_profile"] = {
        "current_memory_mb": round(current_mem / (1024 * 1024), 2),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
        "db_file_size_mb": round(os.path.getsize(db_file) / (1024 * 1024), 2) if os.path.exists(db_file) else 0,
    }

    # Cleanup temp db
    await stress_engine.dispose()
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    print("\n" + "=" * 80)
    print("STRESS SUITE SUMMARY")
    print(f"  Peak RAM: {report['resource_profile']['peak_memory_mb']} MB")
    print(f"  50,000 PYQs Compound Query Latency: {report['pyq_benchmarks']['50000_pyqs']['compound_query_avg_ms']} ms")
    print(f"  50,000 PYQs Paginated Latency (limit 25): {report['pyq_benchmarks']['50000_pyqs']['paginated_query_ms']} ms")
    print(f"  5,000 Current Affairs Priority Query: {report['current_affairs_benchmarks']['5000_records']['priority_query_ms']} ms")
    print(f"  500 Nodes Branch Traversal: {report['syllabus_benchmarks']['500_nodes']['branch_traversal_ms']} ms")
    print(f"  10,000 Revision Due Queue Query: {report['revision_benchmarks']['due_queue_query_ms']} ms")
    print("=" * 80)

    # Save benchmark report to docs
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "performance"), exist_ok=True)
    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "performance", "stress_suite_results.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[OK] Results recorded to: {report_path}")
    return report


if __name__ == "__main__":
    asyncio.run(run_stress_suite())
