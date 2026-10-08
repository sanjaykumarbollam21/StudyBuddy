import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.practice import QuizSession, Question, Answer
from app.models.learning import StudentMastery
from app.models.document import DocumentChunk
from app.practice.types import QuestionType, DifficultyLevel, GeneratedQuestion, PracticeEvaluation
from app.practice.generator import QuestionGenerator
from app.practice.evaluator import AnswerEvaluator
from app.curriculum.service import CurriculumService
from app.tutor.providers import get_llm_provider


def utc_now():
    return datetime.now(timezone.utc)


class PracticeService:
    """
    Coordinates practice sessions, assessment evaluations, evidence-based mastery tracking,
    and weak-area diagnosis.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.llm_provider = get_llm_provider()
        self.generator = QuestionGenerator(self.llm_provider)
        self.evaluator = AnswerEvaluator(self.llm_provider)

    async def start_session(
        self,
        user_id: str,
        topic: str,
        session_mode: str = "practice",  # practice, timed, exam
        count: int = 5,
        difficulty: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initializes a new practice assessment session.
        """
        diff_enum = DifficultyLevel(difficulty.lower()) if difficulty and difficulty.lower() in [d.value for d in DifficultyLevel] else None

        rag_chunks = []
        if document_id and self.db:
            chunks_res = await self.db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            rag_chunks = chunks_res.scalars().all()

        generated = self.generator.generate_questions(
            topic=topic,
            count=count,
            difficulty=diff_enum,
            rag_chunks=rag_chunks,
        )

        session_id = f"qs-{uuid.uuid4().hex[:12]}"
        title = f"{topic} {session_mode.capitalize()} Quiz"

        if self.db:
            quiz_session = QuizSession(
                id=session_id,
                user_id=user_id,
                topic_title=topic,
                title=title,
                total_questions=len(generated),
                session_mode=session_mode,
                current_question_index=0,
                status="in_progress",
            )
            self.db.add(quiz_session)
            await self.db.flush()

            for q in generated:
                db_q = Question(
                    id=q.id,
                    quiz_session_id=session_id,
                    topic_title=topic,
                    question_type=q.question_type.value,
                    prompt=q.prompt,
                    options=q.options,
                    correct_answer=q.correct_answer,
                    explanation=q.explanation,
                    distractor_explanations=q.distractor_explanations,
                    difficulty=q.difficulty.value,
                    learning_objective=q.learning_objective,
                    concept_tag=q.concept_tag,
                    order_index=q.order_index,
                )
                self.db.add(db_q)

            await self.db.commit()

        first_q = generated[0].to_dict() if generated else None
        # Sanitize correct answer & explanations from client for active question
        if first_q:
            first_q.pop("correct_answer", None)
            first_q.pop("explanation", None)
            first_q.pop("distractor_explanations", None)

        return {
            "session_id": session_id,
            "title": title,
            "topic": topic,
            "session_mode": session_mode,
            "total_questions": len(generated),
            "current_question_index": 0,
            "status": "in_progress",
            "current_question": first_q,
        }

    async def submit_answer(
        self,
        user_id: str,
        session_id: str,
        question_id: str,
        student_response: str,
    ) -> Dict[str, Any]:
        """
        Evaluates a submitted student answer, updates evidence-based mastery,
        records weak areas/misconceptions, and returns the next question or final score.
        """
        if not self.db:
            # Offline standalone evaluation
            dummy_q = GeneratedQuestion(
                id=question_id,
                question_type=QuestionType.MCQ,
                prompt="Sample Question",
                correct_answer=student_response,
                explanation="Sample explanation",
            )
            eval_res = await self.evaluator.evaluate(dummy_q, student_response)
            return {
                "evaluation": eval_res.to_dict(),
                "session_score_percentage": 100.0,
                "is_session_completed": True,
                "next_question": None,
            }

        # 1. Fetch Question and Session
        q_res = await self.db.execute(select(Question).where(Question.id == question_id))
        q_record = q_res.scalars().first()
        if not q_record:
            raise ValueError(f"Question {question_id} not found.")

        s_res = await self.db.execute(
            select(QuizSession).where(QuizSession.id == session_id, QuizSession.user_id == user_id)
        )
        session = s_res.scalars().first()
        if not session:
            raise ValueError(f"Quiz session {session_id} not found.")

        # Reconstruct GeneratedQuestion
        gen_q = GeneratedQuestion(
            id=q_record.id,
            question_type=QuestionType(q_record.question_type),
            prompt=q_record.prompt,
            options=q_record.options or [],
            correct_answer=q_record.correct_answer,
            explanation=q_record.explanation,
            distractor_explanations=q_record.distractor_explanations or {},
            difficulty=DifficultyLevel(q_record.difficulty) if q_record.difficulty else DifficultyLevel.INTERMEDIATE,
            learning_objective=q_record.learning_objective or "",
            concept_tag=q_record.concept_tag or "",
            order_index=q_record.order_index,
        )

        # 2. Evaluate answer
        eval_result = await self.evaluator.evaluate(gen_q, student_response)

        # 3. Record Answer in DB
        answer_rec = Answer(
            id=f"ans-{uuid.uuid4().hex[:12]}",
            question_id=question_id,
            user_id=user_id,
            quiz_session_id=session_id,
            student_response=student_response,
            is_correct=eval_result.is_correct,
            score_awarded=eval_result.score,
            evaluation_feedback=eval_result.to_dict(),
        )
        self.db.add(answer_rec)

        # 4. Evidence-based StudentMastery updating
        topic_title = q_record.topic_title or session.topic_title or "General"
        mastery_percentage = await self._update_mastery_from_evidence(
            user_id=user_id,
            topic_title=topic_title,
            eval_result=eval_result,
            prompt=q_record.prompt,
        )

        # 5. Advance session state
        session.current_question_index += 1

        # Calculate session cumulative score
        answers_res = await self.db.execute(
            select(Answer).where(Answer.quiz_session_id == session_id)
        )
        all_answers = answers_res.scalars().all()
        # Include current answer in tally
        scores = [a.score_awarded for a in all_answers] + [eval_result.score]
        session_avg = round((sum(scores) / len(scores)) * 100, 1) if scores else 0.0
        session.score_percentage = session_avg

        # Check if session completed
        is_completed = session.current_question_index >= session.total_questions
        next_question_data = None

        if is_completed:
            session.status = "completed"
            session.completed_at = utc_now()
        else:
            # Fetch next question
            next_q_res = await self.db.execute(
                select(Question)
                .where(Question.quiz_session_id == session_id, Question.order_index == session.current_question_index + 1)
            )
            next_q = next_q_res.scalars().first()
            if next_q:
                next_question_data = {
                    "id": next_q.id,
                    "order_index": next_q.order_index,
                    "question_type": next_q.question_type,
                    "prompt": next_q.prompt,
                    "options": next_q.options,
                    "difficulty": next_q.difficulty,
                    "learning_objective": next_q.learning_objective,
                    "concept_tag": next_q.concept_tag,
                }

        await self.db.commit()

        return {
            "evaluation": eval_result.to_dict(),
            "session_score_percentage": session.score_percentage,
            "updated_mastery_percentage": mastery_percentage,
            "is_session_completed": is_completed,
            "current_question_index": session.current_question_index,
            "total_questions": session.total_questions,
            "next_question": next_question_data,
        }

    async def _update_mastery_from_evidence(
        self,
        user_id: str,
        topic_title: str,
        eval_result: PracticeEvaluation,
        prompt: str,
    ) -> float:
        """
        Updates student mastery with weighted evidence:
        M_new = (M_old * 0.7) + (score * 100 * 0.3)
        Tracks weak areas and misconceptions.
        """
        mastery_res = await self.db.execute(
            select(StudentMastery).where(
                StudentMastery.user_id == user_id,
                StudentMastery.topic_id == topic_title,
            )
        )
        record = mastery_res.scalars().first()

        score_scaled = eval_result.score * 100.0

        if not record:
            new_mastery = round(score_scaled, 1)
            weak_list = []
            if eval_result.score < 0.7:
                weak_list.append({
                    "concept": eval_result.concept_tag or topic_title,
                    "misconception": eval_result.misconception_identified or "Incorrect response",
                    "prompt": prompt[:80],
                    "detected_at": utc_now().isoformat(),
                })

            record = StudentMastery(
                id=f"sm-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                topic_id=topic_title,
                mastery_percentage=new_mastery,
                times_practiced=1,
                consecutive_correct=1 if eval_result.is_correct else 0,
                last_evaluated_at=utc_now(),
                weak_areas=weak_list,
            )
            self.db.add(record)
        else:
            # Weighted update
            old_m = record.mastery_percentage
            new_m = round((old_m * 0.7) + (score_scaled * 0.3), 1)
            record.mastery_percentage = min(100.0, max(0.0, new_m))
            record.times_practiced += 1
            if eval_result.is_correct:
                record.consecutive_correct += 1
            else:
                record.consecutive_correct = 0

            # Log weak area if struggling or distractor chosen
            if eval_result.score < 0.7:
                curr_weak = list(record.weak_areas or [])
                curr_weak.append({
                    "concept": eval_result.concept_tag or topic_title,
                    "misconception": eval_result.misconception_identified or "Incorrect response",
                    "prompt": prompt[:80],
                    "detected_at": utc_now().isoformat(),
                })
                # Keep last 10 weak areas
                record.weak_areas = curr_weak[-10:]

            record.last_evaluated_at = utc_now()

        # If mastery reaches >= 80%, update roadmap milestones
        if record.mastery_percentage >= 80.0:
            curriculum_service = CurriculumService(self.db)
            await curriculum_service.update_progress_from_mastery(
                user_id=user_id,
                topic_title=topic_title,
                mastery_score=record.mastery_percentage,
            )

        return record.mastery_percentage

    async def get_practice_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieves user's historical quiz sessions and performance.
        """
        if not self.db:
            return []

        res = await self.db.execute(
            select(QuizSession)
            .where(QuizSession.user_id == user_id)
            .order_by(QuizSession.created_at.desc())
            .limit(limit)
        )
        sessions = res.scalars().all()

        return [
            {
                "id": s.id,
                "title": s.title,
                "topic": s.topic_title,
                "session_mode": s.session_mode,
                "total_questions": s.total_questions,
                "score_percentage": s.score_percentage,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in sessions
        ]

    async def get_weak_areas(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Aggregates diagnosed weak areas and misconceptions from StudentMastery records,
        providing personalized remediation recommendations.
        """
        if not self.db:
            return []

        res = await self.db.execute(
            select(StudentMastery).where(StudentMastery.user_id == user_id)
        )
        masteries = res.scalars().all()

        weak_areas = []
        for m in masteries:
            is_weak_topic = m.mastery_percentage < 70.0
            logged_misconceptions = m.weak_areas or []

            if is_weak_topic or logged_misconceptions:
                latest_misconception = logged_misconceptions[-1]["misconception"] if logged_misconceptions else "General difficulty on practice problems."
                weak_areas.append({
                    "topic": m.topic_id,
                    "mastery_percentage": m.mastery_percentage,
                    "times_practiced": m.times_practiced,
                    "primary_misconception": latest_misconception,
                    "total_misconceptions_logged": len(logged_misconceptions),
                    "remediation_action": f"Re-teach '{m.topic_id}' with Socratic AI Teacher",
                })

        return weak_areas
