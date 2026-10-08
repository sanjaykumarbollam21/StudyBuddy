import pytest
import asyncio
from app.voice.context_manager import ConversationContextManager, VoiceIntent
from app.multimodal.service import MultimodalService
from app.voice.service import VoiceService


def test_voice_intent_classification():
    cm = ConversationContextManager()

    # 1. Topic explanation
    r1 = cm.classify_voice_intent("Explain deadlocks to me please")
    assert r1["intent"] == VoiceIntent.EXPLAIN_TOPIC
    assert "Deadlock" in r1["extracted_target"]

    # 2. Quiz request
    r2 = cm.classify_voice_intent("Quiz me on this concept")
    assert r2["intent"] == VoiceIntent.QUIZ_ME

    # 3. Hint request
    r3 = cm.classify_voice_intent("Can you give me a hint?")
    assert r3["intent"] == VoiceIntent.HINT

    # 4. Simplification
    r4 = cm.classify_voice_intent("Make it easier, I don't understand")
    assert r4["intent"] == VoiceIntent.SIMPLIFY

    # 5. Page inquiry
    r5 = cm.classify_voice_intent("What is explained on page 42?")
    assert r5["intent"] == VoiceIntent.PAGE_EXPLANATION
    assert r5["page_number"] == 42

    # 6. Image inquiry
    r6 = cm.classify_voice_intent("What does this diagram show?", has_image=True)
    assert r6["intent"] == VoiceIntent.IMAGE_EXPLANATION


def test_multimodal_diagram_and_formula_analysis():
    ms = MultimodalService()

    # Test deadlock diagram analysis
    result = asyncio.run(
        ms.analyze_study_image(
            user_id="user-test-mm",
            current_topic="Deadlocks",
            user_prompt="Explain this diagram of processes and resources",
        )
    )

    assert result["image_type"] == "diagram"
    assert "Deadlock" in result["detected_topic"]
    assert len(result["visual_elements"]) >= 2
    assert "P1" in result["visual_elements"][0] or "Process" in result["visual_elements"][0]
    assert "circular" in result["conceptual_explanation"].lower()
    assert len(result["spoken_script"]) > 20
    assert len(result["check_question"]) > 10
    assert len(result["suggested_voice_prompts"]) >= 2


def test_multimodal_cpu_gantt_and_paging():
    ms = MultimodalService()

    # Test CPU scheduling Gantt chart analysis
    res_cpu = asyncio.run(
        ms.analyze_study_image(
            user_id="user-test-mm",
            current_topic="CPU Scheduling",
            user_prompt="Analyze this timeline chart",
        )
    )
    assert "convoy" in res_cpu["conceptual_explanation"].lower()
    assert "gantt" in res_cpu["title"].lower()

    # Test Memory Management two-level paging analysis
    res_mem = asyncio.run(
        ms.analyze_study_image(
            user_id="user-test-mm",
            current_topic="Memory Management",
            user_prompt="Explain page table partition",
        )
    )
    assert "paging" in res_mem["title"].lower()
    assert "10 bits" in res_mem["conceptual_explanation"] or "offset" in res_mem["conceptual_explanation"].lower()


def test_voice_turn_processing_and_speech_cleaning():
    vs = VoiceService()

    # Test speech script cleaner
    raw_markdown = "### 🎯 Deadlocks\n\n* **Mutual Exclusion**: resource is unshareable.\n```c\nlock();\n```\nWhat's next?"
    cleaned = vs._clean_for_speech(raw_markdown)
    assert "#" not in cleaned
    assert "*" not in cleaned
    assert "🎯" not in cleaned
    assert "Mutual Exclusion: resource is unshareable" in cleaned

    # Test conversational voice turn
    turn_result = asyncio.run(
        vs.process_voice_turn(
            user_id="user-test-voice",
            transcript="Explain deadlocks to me and quiz me",
            current_topic="Deadlocks",
        )
    )

    assert "session_id" in turn_result
    assert len(turn_result["teacher_reply_text"]) > 20
    assert len(turn_result["spoken_text"]) > 20
    assert turn_result["pedagogical_state"] is not None
    assert len(turn_result["suggested_quick_actions"]) >= 1


def test_document_aware_page_grounding():
    vs = VoiceService()

    turn_page = asyncio.run(
        vs.process_voice_turn(
            user_id="user-test-voice",
            transcript="Explain page 42 to me",
            current_topic="Deadlocks",
            page_number=42,
        )
    )

    assert turn_page["intent"] == "page_explanation"
    assert "Page 42" in turn_page["teacher_reply_text"]
    assert "Page 42" in turn_page["concept_title"]
    assert len(turn_page["spoken_text"]) > 10
