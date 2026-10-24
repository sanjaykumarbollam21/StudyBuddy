import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.teaching.state import TeachingState, ConceptStep, StudentDialogueTurn, EvaluationVerdict
from app.teaching.models import TeachingSessionModel, TeacherTurnResponse
from app.teaching.curriculum import get_curriculum_for_topic
from app.teaching.evaluator import AnswerEvaluationService
from app.teaching.remediation import AdaptiveRemediationService
from app.tutor.providers import get_llm_provider, LLMProvider
from app.search.hybrid import KnowledgeSearchService
from app.models.learning import StudentMastery, Topic
from app.models.document import DocumentChunk
from app.teaching.service import TeachingSessionService

# In-memory session store (backed by database sync)
_active_sessions: Dict[str, TeachingSessionModel] = {}

class TeachingEngine:
    """
    Core Pedagogical State Engine for Study Buddy.
    Orchestrates the active teaching loop:
    Assess -> Teach -> Ask -> Evaluate -> Adapt/Remediate -> Re-test -> Advance.
    """

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        search_service: Optional[KnowledgeSearchService] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.db_session = db_session
        self.search_service = search_service
        self.llm_provider = llm_provider or get_llm_provider()
        self.evaluator = AnswerEvaluationService(self.llm_provider)
        self.remediation = AdaptiveRemediationService(self.llm_provider)

    async def start_session(
        self,
        user_id: str,
        topic: str,
        subject: str = "General",
        document_id: Optional[str] = None,
        student_goal: Optional[str] = None,
    ) -> TeacherTurnResponse:
        """
        Initializes a teaching session for a topic or document.
        Retrieves relevant RAG chunks if available and crafts structured concept steps.
        """
        rag_chunks = []
        if self.search_service:
            try:
                search_results = await self.search_service.search_hybrid(
                    user_id=user_id,
                    query=topic,
                    top_k=4,
                    document_ids=[document_id] if document_id else None,
                )
                rag_chunks = search_results
            except Exception:
                rag_chunks = []

        # If document_id was provided and search had no hits or search_service was unavailable, fetch chunks directly
        if document_id and self.db_session and not rag_chunks:
            try:
                stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).limit(4)
                res = await self.db_session.execute(stmt)
                db_chunks = res.scalars().all()
                if db_chunks:
                    rag_chunks = [
                        {
                            "document_id": c.document_id,
                            "document_name": topic,
                            "page_number": c.page_number or 1,
                            "section_title": c.section_title or f"Section {c.chunk_index + 1}",
                            "content": c.content,
                        }
                        for c in db_chunks
                    ]
            except Exception:
                pass

        steps = get_curriculum_for_topic(topic, rag_chunks=rag_chunks)

        session = TeachingSessionModel(
            session_id=f"teach-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            topic=topic,
            subject=subject,
            document_id=document_id,
            current_state=TeachingState.ASSESS_PRIOR_KNOWLEDGE,
            current_step_index=0,
            steps=steps,
            mastery_score=0.0,
        )

        initial_probe = f"Before we start, what do you already know about {topic}?"
        session.dialogue.append(
            StudentDialogueTurn(
                turn_index=0,
                speaker="teacher",
                state=TeachingState.ASSESS_PRIOR_KNOWLEDGE,
                content=initial_probe,
                question=initial_probe,
            )
        )

        await self.save_session(session)

        return TeacherTurnResponse(
            session_id=session.session_id,
            state=session.current_state,
            teacher_message=initial_probe,
            check_question=initial_probe,
            mastery_percentage=0.0,
            current_step_number=1,
            total_steps=len(steps),
            suggested_actions=["I know a little bit", "I am completely new to this", "Just give me the basics"],
            source_citation=steps[0].source_citation if steps else None,
        )

    async def process_student_turn(
        self,
        session_id: str,
        student_answer: str,
        action_type: str = "answer",
    ) -> TeacherTurnResponse:
        """
        Processes student input and advances the pedagogical state machine.
        """
        session = await self.get_session(session_id)
        if not session:
            raise KeyError(f"Teaching session '{session_id}' not found.")

        current_step = session.current_step

        # Record student dialogue turn
        session.dialogue.append(
            StudentDialogueTurn(
                turn_index=len(session.dialogue),
                speaker="student",
                state=session.current_state,
                content=student_answer,
            )
        )

        # STATE 1: If assessing prior knowledge, transition to teaching first concept
        if session.current_state == TeachingState.ASSESS_PRIOR_KNOWLEDGE:
            ans_lower = student_answer.lower()
            if any(term in ans_lower for term in ["stuck", "block", "wait", "freeze", "lock"]):
                acknowledgement = "Good starting point."
            elif any(term in ans_lower for term in ["new", "nothing", "don't know", "no idea"]):
                acknowledgement = "No worries at all! That's why we're here to learn it together."
            else:
                acknowledgement = "Thanks for sharing your intuition."

            session.current_state = TeachingState.CHECK_UNDERSTANDING
            msg = (
                f"{acknowledgement} {current_step.explanation}\n\n"
                f"{current_step.analogy}\n\n"
                f"🎯 Check your understanding:\n"
                f"{current_step.check_question}"
            )

            session.dialogue.append(
                StudentDialogueTurn(
                    turn_index=len(session.dialogue),
                    speaker="teacher",
                    state=TeachingState.CHECK_UNDERSTANDING,
                    content=msg,
                    concept_title=current_step.title,
                    question=current_step.check_question,
                )
            )

            await self.save_session(session)

            return TeacherTurnResponse(
                session_id=session.session_id,
                state=session.current_state,
                teacher_message=msg,
                concept_title=current_step.title,
                explanation=current_step.explanation,
                analogy=current_step.analogy,
                check_question=current_step.check_question,
                mastery_percentage=session.mastery_score,
                current_step_number=session.current_step_index + 1,
                total_steps=session.total_steps,
                suggested_actions=["Give me a hint", "Explain simpler", "I need help"],
                source_citation=current_step.source_citation,
            )

        # STATE 2: Checking understanding or evaluating remediation response
        eval_result = await self.evaluator.evaluate_answer(
            step=current_step,
            student_answer=student_answer,
            action_type=action_type,
        )

        # Check if this turn is an answer to a previous Turn-1 partial follow-up question
        was_partial_followup = getattr(session, "partial_followup_pending", False)
        if was_partial_followup:
            session.partial_followup_pending = False

        # BRANCH A: Student answered correctly OR advanced after partial follow-up/struggle
        if eval_result.verdict == EvaluationVerdict.CORRECT or (
            eval_result.verdict == EvaluationVerdict.PARTIALLY_CORRECT and (session.struggle_count > 0 or was_partial_followup)
        ):
            # If advancing after partial follow-up, award remaining delta (+15% if correct, +5% if partial)
            delta = eval_result.mastery_delta if not was_partial_followup else (15.0 if eval_result.verdict == EvaluationVerdict.CORRECT else 5.0)
            session.mastery_score = max(0.0, min(100.0, session.mastery_score + delta))
            session.struggle_count = 0

            # Advance to next step if available
            if session.current_step_index + 1 < session.total_steps:
                session.current_step_index += 1
                next_step = session.current_step
                session.current_state = TeachingState.CHECK_UNDERSTANDING

                teacher_msg = (
                    f"{eval_result.feedback}\n\n"
                    f"Next, let's look at {next_step.title}:\n\n"
                    f"{next_step.explanation}\n\n"
                    f"{next_step.analogy}\n\n"
                    f"🎯 Check your understanding:\n"
                    f"{next_step.check_question}"
                )

                session.dialogue.append(
                    StudentDialogueTurn(
                        turn_index=len(session.dialogue),
                        speaker="teacher",
                        state=TeachingState.CHECK_UNDERSTANDING,
                        content=teacher_msg,
                        concept_title=next_step.title,
                        question=next_step.check_question,
                        evaluation_verdict=eval_result.verdict,
                        feedback=eval_result.feedback,
                        mastery_delta=delta,
                    )
                )

                await self._persist_mastery(session)
                await self.save_session(session)

                return TeacherTurnResponse(
                    session_id=session.session_id,
                    state=session.current_state,
                    teacher_message=teacher_msg,
                    concept_title=next_step.title,
                    explanation=next_step.explanation,
                    analogy=next_step.analogy,
                    check_question=next_step.check_question,
                    evaluation={
                        "verdict": eval_result.verdict.value,
                        "feedback": eval_result.feedback,
                        "is_correct": True,
                        "source": eval_result.source,
                    },
                    mastery_percentage=session.mastery_score,
                    current_step_number=session.current_step_index + 1,
                    total_steps=session.total_steps,
                    suggested_actions=["Give me a hint", "Explain simpler"],
                    source_citation=next_step.source_citation,
                )
            else:
                # Completed all concept steps!
                session.current_state = TeachingState.COMPLETED
                session.is_completed = True
                session.mastery_score = 100.0

                completion_msg = (
                    f"{eval_result.feedback}\n\n"
                    f"🎓 Outstanding work! You have completely mastered all core concepts of '{session.topic}'.\n\n"
                    f"+ Mastery 100% Complete\n"
                    f"+ All Check Questions Solved\n\n"
                    f"Would you like to practice a quick quiz or move to the next related topic?"
                )

                session.dialogue.append(
                    StudentDialogueTurn(
                        turn_index=len(session.dialogue),
                        speaker="teacher",
                        state=TeachingState.COMPLETED,
                        content=completion_msg,
                        evaluation_verdict=eval_result.verdict,
                        feedback=eval_result.feedback,
                        mastery_delta=delta,
                    )
                )

                await self._persist_mastery(session)
                await self.save_session(session)

                return TeacherTurnResponse(
                    session_id=session.session_id,
                    state=session.current_state,
                    teacher_message=completion_msg,
                    concept_title="Lesson Complete",
                    evaluation={
                        "verdict": eval_result.verdict.value,
                        "feedback": eval_result.feedback,
                        "is_correct": True,
                        "source": eval_result.source,
                    },
                    mastery_percentage=100.0,
                    current_step_number=session.total_steps,
                    total_steps=session.total_steps,
                    is_lesson_completed=True,
                    suggested_actions=["Take a Practice Quiz", "Learn Next Topic", "Review Summary"],
                )

        # BRANCH A2: Turn-1 Partial Correctness (No new state, stay in CHECK_UNDERSTANDING)
        elif eval_result.verdict == EvaluationVerdict.PARTIALLY_CORRECT and session.struggle_count == 0 and not was_partial_followup:
            # Award +10% mastery for partial understanding on the first attempt
            session.mastery_score = max(0.0, min(100.0, session.mastery_score + 10.0))
            session.partial_followup_pending = True

            # Target the first missing key idea
            missing_idea = (eval_result.ideas_missing[0] if eval_result.ideas_missing else "how this applies overall").strip()
            followup_q = f"You're on the right track! Can you explain {missing_idea.lower().rstrip('.')}?"

            feedback_clean = eval_result.feedback.strip()
            # Leak guard: Check if feedback states key ideas or expected core concept
            if self._detect_answer_leak(feedback_clean, current_step):
                feedback_clean = "You've captured part of the core intuition! Let's connect it to the missing piece."

            teacher_msg = (
                f"{feedback_clean}\n\n"
                f"🎯 Quick follow-up question:\n"
                f"{followup_q}"
            )

            session.dialogue.append(
                StudentDialogueTurn(
                    turn_index=len(session.dialogue),
                    speaker="teacher",
                    state=TeachingState.CHECK_UNDERSTANDING,
                    content=teacher_msg,
                    concept_title=current_step.title,
                    question=followup_q,
                    evaluation_verdict=eval_result.verdict,
                    feedback=feedback_clean,
                    mastery_delta=10.0,
                )
            )

            await self._persist_mastery(session)
            await self.save_session(session)

            return TeacherTurnResponse(
                session_id=session.session_id,
                state=session.current_state,
                teacher_message=teacher_msg,
                concept_title=current_step.title,
                explanation=current_step.explanation,
                analogy=current_step.analogy,
                check_question=followup_q,
                evaluation={
                    "verdict": eval_result.verdict.value,
                    "feedback": feedback_clean,
                    "is_correct": False,
                    "source": eval_result.source,
                },
                mastery_percentage=session.mastery_score,
                current_step_number=session.current_step_index + 1,
                total_steps=session.total_steps,
                suggested_actions=["Give me a hint", "Explain simpler"],
                source_citation=current_step.source_citation,
            )

        # BRANCH B: Student struggled, held a misconception, or failed follow-up -> Trigger Remediation
        session.struggle_count += 1
        session.current_state = TeachingState.RETEACHING

        remed = await self.remediation.create_remediation(
            step=current_step,
            student_answer=student_answer,
            misconception=eval_result.misconception_identified,
        )

        # Show one concise feedback line without duplicating re_explanation
        feedback_line = (eval_result.feedback or remed.re_explanation or "Let's revisit this concept.").strip()
        remed_msg = (
            f"{feedback_line}\n\n"
            f"Let's simplify it.\n\n"
            f"{remed.simpler_analogy}\n\n"
            f"🎯 {remed.simpler_question}"
        )

        # Answer Leak Guard: Check if the reply leaks key ideas or expected answer
        leaked_phrase = self._detect_answer_leak(remed_msg, current_step)
        if leaked_phrase:
            # Regenerate once with strict instruction
            remed_retry = await self.remediation.create_remediation(
                step=current_step,
                student_answer=student_answer,
                misconception=eval_result.misconception_identified,
                strict_no_leak=True,
                prohibited_phrase=leaked_phrase,
            )
            fb_leaked = self._detect_answer_leak(feedback_line, current_step)
            retry_feedback = (
                remed_retry.re_explanation.strip()
                if fb_leaked
                else (feedback_line or remed_retry.re_explanation).strip()
            )
            remed_msg_retry = (
                f"{retry_feedback}\n\n"
                f"Let's simplify it.\n\n"
                f"{remed_retry.simpler_analogy}\n\n"
                f"🎯 {remed_retry.simpler_question}"
            )
            # If it STILL leaks, fall back to a safe generic socratic hint/analogy
            if self._detect_answer_leak(remed_msg_retry, current_step):
                remed_msg = (
                    "Not quite! Let's approach this from a simpler, concrete angle.\n\n"
                    "Let's simplify it.\n\n"
                    f"{current_step.simpler_analogy or current_step.analogy}\n\n"
                    f"🎯 Consider how the pieces interact in this scenario. What happens next?"
                )
            else:
                remed_msg = remed_msg_retry
                remed = remed_retry

        session.dialogue.append(
            StudentDialogueTurn(
                turn_index=len(session.dialogue),
                speaker="teacher",
                state=TeachingState.RETEACHING,
                content=remed_msg,
                concept_title=current_step.title,
                question=remed.simpler_question,
                evaluation_verdict=eval_result.verdict,
                feedback=eval_result.feedback,
            )
        )

        await self.save_session(session)

        return TeacherTurnResponse(
            session_id=session.session_id,
            state=session.current_state,
            teacher_message=remed_msg,
            concept_title=current_step.title,
            explanation=remed.re_explanation,
            analogy=remed.simpler_analogy,
            check_question=remed.simpler_question,
            evaluation={
                "verdict": eval_result.verdict.value,
                "feedback": eval_result.feedback,
                "misconception": eval_result.misconception_identified,
                "is_correct": False,
                "source": eval_result.source,
            },
            mastery_percentage=session.mastery_score,
            current_step_number=session.current_step_index + 1,
            total_steps=session.total_steps,
            suggested_actions=["Neither can continue", "Give me a hint", "Try another example"],
            source_citation=current_step.source_citation,
        )

    def _detect_answer_leak(self, text: str, step: ConceptStep) -> Optional[str]:
        """
        Detects whether the teacher message leaks the concept's key ideas verbatim
        or the expected core concept on a wrong or partial attempt.
        """
        text_lower = text.lower()
        candidates = []
        if step.expected_core_concept:
            candidates.append(step.expected_core_concept.lower().strip())
        for idea in (step.key_ideas or []):
            candidates.append(idea.lower().strip())

        for cand in candidates:
            cand_clean = cand.rstrip(".")
            if len(cand_clean) > 15 and cand_clean in text_lower:
                return cand_clean

        # Check for three CAP terms together if CAP topic
        if "cap" in step.title.lower() or "cap" in step.check_question.lower():
            if "consistency, availability, and partition tolerance" in text_lower or (
                "consistency" in text_lower and "availability" in text_lower and "partition tolerance" in text_lower
            ):
                return "consistency, availability, and partition tolerance"

        return None

    async def _persist_mastery(self, session: TeachingSessionModel):
        """Persists updated mastery percentage in the database and updates roadmap progress."""
        if not self.db_session:
            return
        try:
            from app.curriculum.service import CurriculumService
            curriculum_service = CurriculumService(self.db_session)
            await curriculum_service.update_progress_from_mastery(
                user_id=session.user_id,
                topic_title=session.topic,
                mastery_score=session.mastery_score,
            )
        except Exception:
            pass

    async def get_session(self, session_id: str) -> Optional[TeachingSessionModel]:
        """Fetches active teaching session from DB if db_session is provided, or in-memory cache."""
        if self.db_session:
            db_sess = await TeachingSessionService.get_session(self.db_session, session_id)
            if db_sess:
                _active_sessions[session_id] = db_sess
                return db_sess
        return _active_sessions.get(session_id)

    def get_session_sync(self, session_id: str) -> Optional[TeachingSessionModel]:
        """Synchronously retrieves from in-memory cache."""
        return _active_sessions.get(session_id)

    async def save_session(self, session: TeachingSessionModel) -> None:
        """Persists session to database and keeps in-memory cache synced."""
        _active_sessions[session.session_id] = session
        if self.db_session:
            await TeachingSessionService.save_session(self.db_session, session)

