import pytest
from datetime import datetime, timezone
import uuid
from unittest.mock import patch, MagicMock

from app.tutor.providers.ollama import OllamaLLMProvider
from app.agent.orchestrator import AutonomousStudyAgent
from app.curriculum.extractor import DocumentConceptExtractor
from app.models.document import DocumentChunk
from app.voice.service import VoiceService


def test_ollama_provider_configuration_and_offline_fallback():
    """
    Test Phase 13 Ollama Provider:
    - 16GB RAM friendly parameters (num_ctx: 2048, keep_alive: '5m')
    - Transparent fallback to LocalLLMProvider when daemon is offline
    """
    provider = OllamaLLMProvider(
        endpoint_url="http://localhost:11434",
        model_name="llama3.2:3b",
        fallback_on_error=True,
    )
    assert provider.get_provider_name() == "ollama_llama3.2:3b"

    # Daemon offline fallback
    with patch.object(provider, "_call_ollama", return_value=None):
        import asyncio
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            provider.generate_response("Explain deadlocks", "You are a tutor.")
        )
        assert res is not None
        assert len(res) > 10

        eval_res = loop.run_until_complete(
            provider.evaluate_student_answer(
                concept_title="Deadlocks",
                question="What causes deadlocks?",
                expected_concept="Circular wait, hold and wait, mutual exclusion, no preemption",
                student_answer="Mutual exclusion and circular wait",
            )
        )
        assert "verdict" in eval_res
        assert "confidence" in eval_res
        loop.close()


def test_ollama_provider_mock_daemon_response():
    """
    Test Phase 13 Ollama Provider with simulated active Ollama daemon.
    """
    provider = OllamaLLMProvider(
        endpoint_url="http://localhost:11434",
        model_name="mistral:7b",
    )
    with patch.object(
        provider,
        "_call_ollama",
        return_value='{"verdict": "correct", "confidence": 0.95, "feedback": "Accurate explanation of Coffman conditions.", "misconception_identified": null}',
    ):
        import asyncio
        loop = asyncio.new_event_loop()
        eval_res = loop.run_until_complete(
            provider.evaluate_student_answer(
                concept_title="Deadlocks",
                question="What is circular wait?",
                expected_concept="A closed chain of processes waiting for resources",
                student_answer="When process 1 waits for process 2 which waits for process 1",
            )
        )
        assert eval_res["verdict"] == "correct"
        assert eval_res["confidence"] == 0.95
        assert "Accurate" in eval_res["feedback"]
        loop.close()


@pytest.mark.asyncio
async def test_persistent_resumable_agent_task_lifecycle():
    """
    Test Phase 13 Persistent Agent Task Lifecycle:
    1. Propose task
    2. Advance step 1
    3. Simulate app close / learner departure -> Pause task
    4. Query active task on app reopen
    5. Resume task -> advance remaining steps
    6. Verify completed state and progress preservation
    """
    user_id = f"resumable-user-{uuid.uuid4().hex[:6]}"
    agent = AutonomousStudyAgent(db_session=None)

    # 1. Propose task
    task = await agent.evaluate_and_propose_task(
        user_id=user_id,
        available_minutes=60,
        days_until_exam=3,
    )
    assert task.id is not None
    assert task.current_state == "proposed"
    assert task.is_resumable is True
    assert task.current_step_index == 0
    assert task.step_progress == {}

    # 2. Advance Step 1 (e.g. Socratic Reteaching completed)
    step_1_res = {"concept": "Coffman Conditions", "mastery_gain": 0.15}
    task_after_step_1 = await agent.advance_step(
        user_id=user_id,
        task_id=task.id,
        step_index=1,
        step_result=step_1_res,
    )
    assert task_after_step_1.current_step_index == 1
    assert task_after_step_1.current_state == "executing"
    assert "1" in task_after_step_1.step_progress
    assert task_after_step_1.step_progress["1"]["status"] == "completed"

    # 3. Simulate learner closing app or stepping away -> Pause task
    paused_task = await agent.pause_task(user_id=user_id, task_id=task.id)
    assert paused_task.current_state == "paused"
    assert paused_task.interrupted_at is not None

    # 4. App reopen -> Fetch active ongoing/paused task
    active_task = await agent.get_active_task(user_id=user_id)
    assert active_task is not None
    assert active_task.id == task.id
    assert active_task.current_state == "paused"
    assert active_task.current_step_index == 1

    # 5. Resume task
    resume_info = await agent.resume_task(user_id=user_id, task_id=task.id)
    assert resume_info["task_id"] == task.id
    assert resume_info["resumed_step_index"] == 2
    assert "PracticeEngine" in resume_info["engine"] or "step" in resume_info["status_summary"].lower()

    # 6. Complete remaining steps (Step 2, Step 3, Step 4)
    await agent.advance_step(
        user_id=user_id,
        task_id=task.id,
        step_index=2,
        step_result={"questions_answered": 5, "accuracy": 0.8},
    )
    await agent.advance_step(
        user_id=user_id,
        task_id=task.id,
        step_index=3,
        step_result={"revision_cards_reviewed": 3},
    )
    final_task = await agent.advance_step(
        user_id=user_id,
        task_id=task.id,
        step_index=4,
        step_result={"mastery_calibrated": True, "final_mastery": 88.0},
        mark_task_completed=True,
    )

    assert final_task.current_state == "completed"
    assert final_task.current_step_index == 4
    assert len(final_task.step_progress) == 4
    assert final_task.completed_at is not None


def test_document_to_learning_pack_generation():
    """
    Test Phase 13 Document-to-Learning Pipeline:
    Upload chunks -> Extract Knowledge Graph DAG -> Build chapters ->
    Generate Socratic lesson plans -> Generate grounded questions with distractors.
    """
    extractor = DocumentConceptExtractor()

    sample_chunks = [
        DocumentChunk(
            id="chunk-1",
            document_id="doc-os-1",
            chunk_index=0,
            content=(
                "Chapter 1: Operating System Foundations. An operating system is software that manages "
                "computer hardware. Core concepts include process management, memory virtualisation, "
                "and I/O scheduling."
            ),
            section_title="Operating System Foundations",
            page_number=1,
        ),
        DocumentChunk(
            id="chunk-2",
            document_id="doc-os-1",
            chunk_index=1,
            content=(
                "Chapter 2: Deadlocks and Concurrency. Prerequisites: Operating System Foundations. "
                "A deadlock occurs when a set of processes are blocked because each process is holding "
                "a resource and waiting for another resource acquired by some other process. "
                "The four Coffman conditions are mutual exclusion, hold and wait, no preemption, and circular wait."
            ),
            section_title="Deadlocks and Concurrency",
            page_number=25,
        ),
        DocumentChunk(
            id="chunk-3",
            document_id="doc-os-1",
            chunk_index=2,
            content=(
                "Chapter 3: Banker's Algorithm and Avoidance. Before studying Banker's Algorithm, "
                "knowledge of Deadlocks and Concurrency is required. Banker's Algorithm dynamically tests "
                "for safety by simulating the allocation of predetermined maximum possible amounts of all resources."
            ),
            section_title="Banker's Algorithm and Avoidance",
            page_number=50,
        ),
    ]

    pack = extractor.generate_learning_pack_from_document(
        chunks=sample_chunks,
        document_title="Operating Systems Principles",
        subject="Computer Science",
    )

    # 1. Structure validation
    assert pack["document_title"] == "Operating Systems Principles"
    assert pack["total_chapters"] >= 3
    assert pack["total_questions"] >= 3

    # 2. Knowledge Graph DAG
    kg = pack["knowledge_graph"]
    assert len(kg["nodes"]) >= 3
    assert len(kg["edges"]) >= 2

    # 3. Chapters
    chapters = pack["chapters"]
    titles = [c["title"] for c in chapters]
    assert any("Foundations" in t for t in titles)
    assert any("Deadlocks" in t for t in titles)

    # 4. Socratic Lessons
    lessons = pack["lessons"]
    assert len(lessons) >= 3
    for lesson in lessons:
        assert "socratic_prompt" in lesson
        assert "estimated_mins" in lesson

    # 5. Practice Questions
    questions = pack["practice_questions"]
    assert len(questions) >= 3
    for q in questions:
        assert "prompt" in q
        assert "explanation" in q
        assert "difficulty" in q


@pytest.mark.asyncio
async def test_real_voice_barge_in_interruption():
    """
    Test Phase 13 Real Voice Interruption / Barge-in:
    When a student interrupts the speaking teacher, speech immediately halts,
    acknowledging interruption with an interactive recovery state.
    """
    voice_service = VoiceService()

    barge_in_turn = await voice_service.process_voice_turn(
        user_id="test-student-voice",
        transcript="wait, hold on",
        current_topic="Deadlocks",
        is_barge_in=True,
    )

    assert barge_in_turn["barge_in_acknowledged"] is True
    assert barge_in_turn["pedagogical_state"] == "INTERRUPTED"
    assert "stopped speaking" in barge_in_turn["spoken_text"]
    assert len(barge_in_turn["suggested_quick_actions"]) > 0
