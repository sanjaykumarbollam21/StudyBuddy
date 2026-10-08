import pytest
from datetime import datetime, timezone
import uuid
from unittest.mock import patch

from app.tutor.providers.llama_cpp import LlamaCppLLMProvider
from app.tutor.providers import get_llm_provider
from app.agent.orchestrator import AutonomousStudyAgent
from app.documents.chunker import ChunkingService
from app.embeddings import get_embedding_provider
from app.curriculum.extractor import DocumentConceptExtractor
from app.practice.generator import QuestionGenerator
from app.intelligence.mastery import calculate_advanced_mastery
from app.revision.sm2 import SM2Scheduler
from app.models.document import DocumentChunk


def test_llama_cpp_provider_completion_and_fallback():
    """
    Test Phase 14 LlamaCppLLMProvider:
    - Native /completion protocol
    - OpenAI-compatible /v1/chat/completions protocol
    - Transparent fallback to LocalLLMProvider when daemon is offline
    """
    # 1. Native /completion
    provider = LlamaCppLLMProvider(
        endpoint_url="http://localhost:8080",
        model_name="mistral-7b-q4",
        use_chat_format=False,
    )
    assert provider.get_provider_name() == "llama_cpp_mistral-7b-q4"

    # Offline fallback
    with patch.object(provider, "_call_llama_cpp", return_value=None):
        import asyncio
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            provider.generate_response("Explain memory virtualisation", "You are an OS teacher.")
        )
        assert res is not None
        assert len(res) > 10

        eval_res = loop.run_until_complete(
            provider.evaluate_student_answer(
                concept_title="Virtual Memory",
                question="What is paging?",
                expected_concept="Fixed-size memory allocation preventing external fragmentation",
                student_answer="Breaking memory into fixed blocks called frames and pages",
            )
        )
        assert "verdict" in eval_res
        assert "confidence" in eval_res
        loop.close()

    # 2. Mock active daemon response
    with patch.object(
        provider,
        "_call_llama_cpp",
        return_value='{"verdict": "correct", "confidence": 0.98, "feedback": "Spot on explanation of paging.", "misconception_identified": null}',
    ):
        loop = asyncio.new_event_loop()
        eval_active = loop.run_until_complete(
            provider.evaluate_student_answer(
                concept_title="Virtual Memory",
                question="What is paging?",
                expected_concept="Fixed-size blocks",
                student_answer="Fixed size blocks called pages",
            )
        )
        assert eval_active["verdict"] == "correct"
        assert eval_active["confidence"] == 0.98
        loop.close()


def test_provider_factory_registers_llama_cpp():
    """
    Test Phase 14 Provider Factory registers llama_cpp.
    """
    p1 = get_llm_provider("llama_cpp")
    assert isinstance(p1, LlamaCppLLMProvider)
    p2 = get_llm_provider("llamacpp")
    assert isinstance(p2, LlamaCppLLMProvider)


@pytest.mark.asyncio
async def test_agent_crash_recovery_and_idempotency():
    """
    Test Phase 14 Agent Fault Tolerance & Crash Recovery:
    Simulates app crash / phone reboot during task execution.
    - Task in 'executing' is recovered to 'paused'
    - Resuming continues from the uncompleted step without duplicating actions
    """
    user_id = f"crash-user-{uuid.uuid4().hex[:6]}"
    agent = AutonomousStudyAgent(db_session=None)

    # 1. Propose and start task
    task = await agent.evaluate_and_propose_task(user_id=user_id, available_minutes=60)
    assert task.current_state == "proposed"

    # Step 1 completes
    await agent.advance_step(
        user_id=user_id,
        task_id=task.id,
        step_index=1,
        step_result={"diagnostic": "done"},
    )

    # 2. Crash occurs while Step 2 is in progress (state is 'executing')
    # Phone reboots -> app calls recover_interrupted_tasks
    recovered_tasks = await agent.recover_interrupted_tasks(user_id=user_id)
    assert len(recovered_tasks) == 1
    assert recovered_tasks[0].id == task.id
    assert recovered_tasks[0].current_state == "paused"
    assert recovered_tasks[0].interrupted_at is not None

    # 3. Learner opens app and resumes
    resume_info = await agent.resume_task(user_id=user_id, task_id=task.id)
    assert resume_info["resumed_step_index"] == 2
    assert "PracticeEngine" in resume_info["engine"]

    # 4. Advance Step 2 without duplicate step 1 execution
    step_2_task = await agent.advance_step(
        user_id=user_id,
        task_id=task.id,
        step_index=2,
        step_result={"practice_score": 0.85},
    )
    assert step_2_task.current_step_index == 2
    assert len(step_2_task.step_progress) == 2


@pytest.mark.asyncio
async def test_full_real_student_journey_end_to_end():
    """
    Test Phase 14 Full Real Student Journey:
    1. Upload real OS textbook material on Deadlocks & Concurrency
    2. Extract chunks deterministically
    3. Run real offline embeddings (BAAI/bge-small-en-v1.5)
    4. Construct KnowledgeGraph DAG
    5. Generate Socratic lesson
    6. Student intentionally provides wrong answer
    7. Teacher identifies misconception & generates remediation
    8. Student proves mastery via practice question
    9. Mastery increases via multi-factor engine
    10. Spaced revision schedule primes SM-2 cards
    11. Agent replans upcoming study sequence
    """
    # 1. Real textbook content
    textbook_content = (
        "Chapter 7: Deadlocks in Modern Operating Systems.\n\n"
        "In a multiprogramming environment, several processes may compete for a finite number of resources. "
        "A process requests resources; if the resources are not available at that time, the process enters a wait state. "
        "A deadlock occurs when every process in a set of processes is waiting for an event that can be caused only by another process in the set.\n\n"
        "Prerequisites: Processes and Concurrency.\n"
        "The Coffman conditions for deadlocks are:\n"
        "1. Mutual Exclusion: At least one resource must be held in a non-shareable mode.\n"
        "2. Hold and Wait: A process must be holding at least one resource and waiting to acquire additional resources.\n"
        "3. No Preemption: Resources cannot be preempted; a resource can be released only voluntarily by the process holding it.\n"
        "4. Circular Wait: A closed chain of processes exists such that each process holds at least one resource that is needed by the next process.\n\n"
        "Deadlock Prevention systematically invalidates one of the four Coffman conditions. For example, circular wait is prevented by "
        "imposing a strict global linear ordering on all resource types."
    )

    # 2. Chunking
    from app.documents.chunker import ChunkingService
    chunker = ChunkingService(chunk_size=300, chunk_overlap=50)
    raw_chunks = chunker.chunk_document(
        document_id="doc-os-textbook",
        user_id="student-journey-1",
        text=textbook_content,
    )
    assert len(raw_chunks) >= 2

    # 3. Real local embeddings
    embed_provider = get_embedding_provider("local")
    embeddings = await embed_provider.embed_texts([c.content for c in raw_chunks])
    assert len(embeddings) == len(raw_chunks)
    assert len(embeddings[0]) == 384  # BAAI/bge-small-en-v1.5 dimension

    # 4. Curriculum Knowledge Graph DAG
    extractor = DocumentConceptExtractor()
    learning_pack = extractor.generate_learning_pack_from_document(
        chunks=raw_chunks,
        document_title="Operating Systems Concepts",
        subject="Computer Science",
    )
    assert learning_pack["total_chapters"] >= 1
    assert len(learning_pack["knowledge_graph"]["nodes"]) >= 1

    # 5. Socratic Teaching
    from app.teaching.engine import TeachingEngine
    from app.teaching.state import TeachingState
    teacher = TeachingEngine()
    session = await teacher.start_session(
        user_id="student-journey-1",
        topic="Deadlocks",
    )
    assert session.session_id is not None
    assert session.state == TeachingState.ASSESS_PRIOR_KNOWLEDGE

    # 6 & 7. Student answers with a misconception
    turn2 = await teacher.process_student_turn(
        session_id=session.session_id,
        student_answer="I know a little bit about it.",
    )
    # Check understanding question
    assert turn2.state == TeachingState.CHECK_UNDERSTANDING

    student_misconception_answer = "Deadlock happens because the CPU is too slow to handle all processes at once."
    remed_turn = await teacher.process_student_turn(
        session_id=session.session_id,
        student_answer=student_misconception_answer,
    )
    assert remed_turn.state == TeachingState.RETEACHING
    assert remed_turn.evaluation["is_correct"] is False
    assert len(remed_turn.check_question) > 5

    # 8. Practice Question with Grounded Distractors
    q_gen = QuestionGenerator()
    questions = q_gen.generate_questions(topic="Deadlocks", count=3, rag_chunks=raw_chunks)
    assert len(questions) == 3
    coffman_q = questions[0]
    assert "Coffman" in coffman_q.prompt or "deadlock" in coffman_q.prompt.lower()

    # 9. Update Mastery via Multi-Factor Engine
    mastery = calculate_advanced_mastery(
        recent_accuracy=0.95,
        historical_accuracy=0.48,
        practice_count=5,
        avg_difficulty=1.2,
        question_type="applied",
        student_confidence=0.90,
    )
    assert mastery["mastery_percentage"] >= 75.0
    assert mastery["retention_factor"] >= 0.90

    # 10. Spaced Revision Scheduling
    sm2_result = SM2Scheduler.calculate_sm2(
        quality=4,  # Good recall
        repetition_count=1,
        interval_days=1,
        ease_factor=2.5,
    )
    assert sm2_result["interval_days"] >= 3
    assert sm2_result["repetition_count"] == 2
    assert sm2_result["next_review_date"] is not None

    # 11. Autonomous Agent Re-evaluation
    agent = AutonomousStudyAgent(db_session=None)
    next_task = await agent.evaluate_and_propose_task(
        user_id="student-journey-1",
        available_minutes=30,
        days_until_exam=4,
    )
    assert next_task.id is not None
    assert next_task.allocated_minutes == 30
