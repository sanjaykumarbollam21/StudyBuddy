import time
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.performance import perf_tracker, async_perf_tracker, perf_store
from app.core.database import AsyncSessionLocal, engine, Base
from app.models import (
    User, Document, DocumentChunk, StudentMastery, RevisionItem, AgentTask, StudyPlan
)

from app.embeddings import get_embedding_provider
from app.teaching.engine import TeachingEngine
from app.teaching.state import TeachingState
from app.tutor.providers.local import LocalLLMProvider
from app.tutor.providers.mock import MockLLMProvider
from app.practice import QuestionGenerator
from app.revision import SM2Scheduler, RevisionService
from app.planner.engine import StudyPlannerEngine
from app.agent.decision import AgentDecisionEngine
from app.documents.chunker import ChunkingService

async def run_profiling():
    results = {}
    print("--- 0. INITIALIZING DB TABLES ---")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("--- 1. PROFILING DATABASE QUERIES ---")
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        # DB: User query
        t0 = time.perf_counter()
        res = await db.execute(select(User).limit(10))
        _ = res.scalars().all()
        results["db_user_query_ms"] = (time.perf_counter() - t0) * 1000

        # DB: Document query
        t0 = time.perf_counter()
        res = await db.execute(select(Document).limit(10))
        _ = res.scalars().all()
        results["db_document_query_ms"] = (time.perf_counter() - t0) * 1000

        # DB: Chunk query
        t0 = time.perf_counter()
        res = await db.execute(select(DocumentChunk).limit(50))
        _ = res.scalars().all()
        results["db_chunk_query_ms"] = (time.perf_counter() - t0) * 1000

        # DB: Mastery query
        t0 = time.perf_counter()
        res = await db.execute(select(StudentMastery).limit(20))
        _ = res.scalars().all()
        results["db_mastery_query_ms"] = (time.perf_counter() - t0) * 1000

        # DB: Revision query
        t0 = time.perf_counter()
        res = await db.execute(select(RevisionItem).limit(20))
        _ = res.scalars().all()
        results["db_revision_query_ms"] = (time.perf_counter() - t0) * 1000

        # DB: Agent task query
        t0 = time.perf_counter()
        res = await db.execute(select(AgentTask).limit(10))
        _ = res.scalars().all()
        results["db_agent_task_query_ms"] = (time.perf_counter() - t0) * 1000

    print("--- 2. PROFILING EMBEDDINGS & VECTOR RETRIEVAL ---")
    provider = get_embedding_provider("local")
    # Embedding: single query
    t0 = time.perf_counter()
    embed = await provider.embed_text("What causes deadlocks in operating systems?")
    results["embedding_single_query_ms"] = (time.perf_counter() - t0) * 1000

    # Embedding: batch 5 texts
    texts = [f"Operating systems concept chunk {i} discussing process scheduling and virtual memory allocation." for i in range(5)]
    t0 = time.perf_counter()
    batch_embeds = await provider.embed_texts(texts)
    results["embedding_batch_5_ms"] = (time.perf_counter() - t0) * 1000

    # Vector cosine similarity benchmarks
    import numpy as np
    q_vec = np.array(embed, dtype=np.float32)

    for chunk_count in [100, 1000, 10000]:
        # Generate random normalized 384-dim vectors
        matrix = np.random.randn(chunk_count, 384).astype(np.float32)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

        # Baseline Python loop simulation
        t0 = time.perf_counter()
        py_scores = []
        for i in range(chunk_count):
            row = matrix[i]
            sim = float(np.dot(q_vec, row))
            py_scores.append(sim)
        results[f"vector_search_{chunk_count}_chunks_python_loop_ms"] = (time.perf_counter() - t0) * 1000

        # Vectorized NumPy matrix multiplication
        t0 = time.perf_counter()
        np_scores = np.dot(matrix, q_vec)
        results[f"vector_search_{chunk_count}_chunks_vectorized_ms"] = (time.perf_counter() - t0) * 1000

    print("--- 3. PROFILING TEACHING, PRACTICE & REVISION ENGINES ---")
    # Teaching Engine response
    teaching_engine = TeachingEngine(llm_provider=LocalLLMProvider())
    t0 = time.perf_counter()
    turn = await teaching_engine.start_session(user_id="perf_test", topic="Deadlocks")
    results["teaching_start_session_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    turn2 = await teaching_engine.process_student_turn(
        session_id=turn.session_id,
        student_answer="Because each process waits for a resource held by another."
    )
    results["teaching_process_turn_ms"] = (time.perf_counter() - t0) * 1000

    # Question generator
    q_gen = QuestionGenerator()
    t0 = time.perf_counter()
    questions = q_gen.generate_questions(topic="CPU Scheduling", count=3)
    results["practice_question_gen_ms"] = (time.perf_counter() - t0) * 1000

    # Spaced Repetition calculation
    scheduler = SM2Scheduler()
    t0 = time.perf_counter()
    calc = scheduler.calculate_sm2(quality=4, repetition_count=1, interval_days=1, ease_factor=2.5)
    results["spaced_repetition_calc_ms"] = (time.perf_counter() - t0) * 1000

    print("--- 4. PROFILING PLANNER & AUTONOMOUS AGENT ---")
    planner = StudyPlannerEngine()
    t0 = time.perf_counter()
    async with AsyncSessionLocal() as db:
        planner.db = db
        plan = await planner.create_plan(
            user_id="perf_test",
            subject="Operating Systems",
            days_until_exam=14,
            daily_study_minutes=120
        )
    results["planner_synthesis_ms"] = (time.perf_counter() - t0) * 1000

    agent = AgentDecisionEngine()
    t0 = time.perf_counter()
    decision = agent.evaluate_highest_value_task(
        available_minutes=45,
        days_until_exam=12,
        due_revision_count=3
    )
    results["agent_decision_ms"] = (time.perf_counter() - t0) * 1000

    print("--- 5. PROFILING DOCUMENT CHUNKING ---")
    sample_text = "Operating Systems Principles\n" * 500
    chunker = ChunkingService(chunk_size=400, chunk_overlap=50)
    t0 = time.perf_counter()
    chunks = chunker.chunk_document(document_id="doc_1", user_id="u_1", text=sample_text)
    results["chunking_500lines_ms"] = (time.perf_counter() - t0) * 1000

    print("\n=== BASELINE PROFILING MEASUREMENTS ===")
    for k, v in results.items():
        print(f"{k}: {v:.2f} ms")

    return results

if __name__ == "__main__":
    asyncio.run(run_profiling())
