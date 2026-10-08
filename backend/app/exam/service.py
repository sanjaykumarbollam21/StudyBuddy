from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.exam import ExamConfig, MockExamSession
from app.models.learning import StudentMastery
from app.models.revision import RevisionItem
from app.exam.generator import ExamGenerator, DEFAULT_BLUEPRINTS
from app.exam.readiness import ReadinessEngine


def utc_now():
    return datetime.now(timezone.utc)


class ExamService:
    """
    Orchestrates Exam Blueprint configuration, timed Mock Exam sessions with negative marking,
    post-exam cognitive intelligence, closed-loop Socratic reteach handoffs, and multi-factor
    Exam Readiness scores.
    """

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        exam_generator: Optional[ExamGenerator] = None,
        readiness_engine: Optional[ReadinessEngine] = None,
    ):
        self.db = db_session
        self.generator = exam_generator or ExamGenerator()
        self.readiness_engine = readiness_engine or ReadinessEngine()

    async def get_or_create_default_config(self, user_id: str, subject: str = "Operating Systems") -> ExamConfig:
        if self.db:
            result = await self.db.execute(
                select(ExamConfig).where(
                    ExamConfig.user_id == user_id,
                    ExamConfig.subject.ilike(f"%{subject}%")
                )
            )
            config = result.scalars().first()
            if config:
                return config

        bp = self.generator.get_default_blueprint(subject)
        exam_date = utc_now() + timedelta(days=21)  # Target: 3 weeks out
        config = ExamConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=f"{subject} Semester Exam",
            subject=subject,
            exam_date=exam_date,
            total_marks=100,
            duration_minutes=60,
            passing_percentage=40.0,
            negative_marking_ratio=0.25,
            blueprint=bp,
            difficulty_mix={"beginner": 0.3, "intermediate": 0.5, "advanced": 0.2},
        )
        if self.db:
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        return config

    async def get_configs(self, user_id: str) -> List[ExamConfig]:
        if not self.db:
            return [await self.get_or_create_default_config(user_id, "Operating Systems")]

        result = await self.db.execute(
            select(ExamConfig).where(ExamConfig.user_id == user_id)
        )
        configs = list(result.scalars().all())
        if not configs:
            default_cfg = await self.get_or_create_default_config(user_id, "Operating Systems")
            return [default_cfg]
        return configs

    async def create_or_update_config(
        self,
        user_id: str,
        title: str,
        subject: str,
        total_marks: int = 100,
        duration_minutes: int = 60,
        negative_marking_ratio: float = 0.25,
        blueprint: Optional[Dict[str, float]] = None,
        difficulty_mix: Optional[Dict[str, float]] = None,
        exam_date: Optional[datetime] = None,
        config_id: Optional[str] = None,
    ) -> ExamConfig:
        bp = blueprint or self.generator.get_default_blueprint(subject)
        mix = difficulty_mix or {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.2}

        if self.db and config_id:
            res = await self.db.execute(
                select(ExamConfig).where(ExamConfig.id == config_id, ExamConfig.user_id == user_id)
            )
            cfg = res.scalars().first()
            if cfg:
                cfg.title = title
                cfg.subject = subject
                cfg.total_marks = total_marks
                cfg.duration_minutes = duration_minutes
                cfg.negative_marking_ratio = negative_marking_ratio
                cfg.blueprint = bp
                cfg.difficulty_mix = mix
                if exam_date:
                    cfg.exam_date = exam_date
                await self.db.commit()
                await self.db.refresh(cfg)
                return cfg

        cfg = ExamConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            subject=subject,
            exam_date=exam_date or (utc_now() + timedelta(days=21)),
            total_marks=total_marks,
            duration_minutes=duration_minutes,
            passing_percentage=40.0,
            negative_marking_ratio=negative_marking_ratio,
            blueprint=bp,
            difficulty_mix=mix,
        )
        if self.db:
            self.db.add(cfg)
            await self.db.commit()
            await self.db.refresh(cfg)
        return cfg

    async def start_mock_exam(
        self,
        user_id: str,
        config_id: Optional[str] = None,
        subject: str = "Operating Systems",
        total_questions: int = 10,
    ) -> MockExamSession:
        cfg = None
        if self.db and config_id:
            res = await self.db.execute(
                select(ExamConfig).where(ExamConfig.id == config_id, ExamConfig.user_id == user_id)
            )
            cfg = res.scalars().first()

        if not cfg:
            cfg = await self.get_or_create_default_config(user_id, subject)

        questions = self.generator.generate_exam_questions(
            subject=cfg.subject,
            blueprint=cfg.blueprint,
            total_questions=total_questions,
            total_marks=float(cfg.total_marks),
            difficulty_mix=cfg.difficulty_mix,
            negative_marking_ratio=cfg.negative_marking_ratio,
        )

        session = MockExamSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            exam_config_id=cfg.id,
            title=f"{cfg.title} — Mock Session",
            subject=cfg.subject,
            duration_minutes=cfg.duration_minutes,
            time_remaining_seconds=cfg.duration_minutes * 60,
            status="in_progress",
            total_questions=len(questions),
            total_marks=float(cfg.total_marks),
            questions_data=questions,
            review_flags=[],
            answers_record={},
            detailed_analysis={},
        )
        if self.db:
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def get_mock_session(self, user_id: str, session_id: str) -> Optional[MockExamSession]:
        if not self.db:
            return None
        res = await self.db.execute(
            select(MockExamSession).where(
                MockExamSession.id == session_id,
                MockExamSession.user_id == user_id
            )
        )
        return res.scalars().first()

    async def save_mock_progress(
        self,
        user_id: str,
        session_id: str,
        answers: Dict[str, Any],
        review_flags: List[str],
        time_remaining_seconds: int,
    ) -> MockExamSession:
        session = await self.get_mock_session(user_id, session_id)
        if not session:
            raise ValueError("Mock exam session not found.")

        if session.status != "in_progress":
            return session

        session.answers_record = answers
        session.review_flags = review_flags
        session.time_remaining_seconds = max(0, time_remaining_seconds)
        if self.db:
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def submit_mock_exam(
        self,
        user_id: str,
        session_id: str,
        answers: Optional[Dict[str, Any]] = None,
        time_spent_seconds: Optional[int] = None,
        in_memory_session: Optional[MockExamSession] = None,
    ) -> MockExamSession:
        session = in_memory_session or (await self.get_mock_session(user_id, session_id))
        if not session:
            raise ValueError("Mock exam session not found.")

        final_answers = answers if answers is not None else (session.answers_record or {})
        questions = session.questions_data or []

        # Find ExamConfig for negative marking ratio
        neg_ratio = 0.25
        cfg = None
        if self.db and session.exam_config_id:
            res = await self.db.execute(
                select(ExamConfig).where(ExamConfig.id == session.exam_config_id)
            )
            cfg = res.scalars().first()
            if cfg:
                neg_ratio = cfg.negative_marking_ratio

        # Evaluate Question by Question
        total_awarded = 0.0
        total_deducted = 0.0
        unanswered_count = 0
        correct_count = 0
        incorrect_count = 0

        # Topic breakdown accumulator
        topic_scores: Dict[str, Dict[str, float]] = {}
        detected_misconceptions: List[Dict[str, Any]] = []

        for q in questions:
            q_id = q["id"]
            topic = q.get("topic", "General")
            q_marks = float(q.get("marks", 10.0))
            q_neg = float(q.get("negative_marks", q_marks * neg_ratio))
            correct_ans = str(q.get("correct_answer", "")).strip().lower()

            if topic not in topic_scores:
                topic_scores[topic] = {"obtained": 0.0, "total": 0.0, "correct": 0, "count": 0}
            topic_scores[topic]["total"] += q_marks
            topic_scores[topic]["count"] += 1

            student_entry = final_answers.get(q_id, {})
            if isinstance(student_entry, dict):
                student_resp = str(student_entry.get("response", "")).strip()
            else:
                student_resp = str(student_entry).strip()

            if not student_resp:
                # Unanswered: 0 marks, NO negative penalty
                unanswered_count += 1
                continue

            # Evaluate response
            is_correct = self._is_answer_correct(q, student_resp, correct_ans)

            if is_correct:
                total_awarded += q_marks
                topic_scores[topic]["obtained"] += q_marks
                topic_scores[topic]["correct"] += 1
                correct_count += 1
            else:
                total_deducted += q_neg
                topic_scores[topic]["obtained"] = max(0.0, topic_scores[topic]["obtained"] - q_neg)
                incorrect_count += 1

                # Check distractor misconception
                distractors = q.get("distractor_explanations", {})
                for distractor_text, explanation in distractors.items():
                    if distractor_text.lower() in student_resp.lower() or student_resp.lower() in distractor_text.lower():
                        detected_misconceptions.append({
                            "question_id": q_id,
                            "topic": topic,
                            "concept_tag": q.get("concept_tag"),
                            "chosen_distractor": distractor_text,
                            "misconception_explanation": explanation,
                        })
                        break

        net_marks = max(0.0, round(total_awarded - total_deducted, 2))
        score_pct = round((net_marks / session.total_marks) * 100.0, 1) if session.total_marks > 0 else 0.0

        # Topic categorization & visual progress bars
        topic_analysis: List[Dict[str, Any]] = []
        weak_topics: List[str] = []
        critical_topics: List[str] = []
        strong_topics: List[str] = []

        for topic, stats in topic_scores.items():
            tot = stats["total"] if stats["total"] > 0 else 1.0
            t_pct = max(0.0, round((stats["obtained"] / tot) * 100.0, 1))

            if t_pct >= 80.0:
                tier = "Strong"
                strong_topics.append(topic)
            elif t_pct >= 65.0:
                tier = "Good"
            elif t_pct >= 40.0:
                tier = "Weak"
                weak_topics.append(topic)
            else:
                tier = "Critical"
                critical_topics.append(topic)

            topic_analysis.append({
                "topic": topic,
                "score_percentage": t_pct,
                "tier": tier,
                "correct_count": int(stats["correct"]),
                "question_count": int(stats["count"]),
                "marks_obtained": round(stats["obtained"], 1),
                "total_marks": round(stats["total"], 1),
            })

        # Generate cognitive diagnosis
        cognitive_diagnosis = self._generate_cognitive_diagnosis(
            topic_scores=topic_analysis,
            misconceptions=detected_misconceptions,
            unanswered_count=unanswered_count,
            total_questions=len(questions),
        )

        # Formulate one-tap closed loop remediation recommendation
        primary_remediate_topic = (
            critical_topics[0] if critical_topics else (weak_topics[0] if weak_topics else "Deadlocks")
        )
        remediation_action = {
            "target_topic": primary_remediate_topic,
            "cta_title": f"Reteach {primary_remediate_topic}",
            "prompt": f"I struggled with {primary_remediate_topic} in my mock exam. Please teach me the core concepts step-by-step and test my understanding.",
            "learning_objective": f"Remediate foundational misconceptions in {primary_remediate_topic} identified during mock exam.",
        }

        # Update StudentMastery in database if available
        if self.db:
            for t_info in topic_analysis:
                topic_name = t_info["topic"]
                t_score = t_info["score_percentage"]
                sm_res = await self.db.execute(
                    select(StudentMastery).where(
                        StudentMastery.user_id == user_id,
                        StudentMastery.topic_id == topic_name
                    )
                )
                sm = sm_res.scalars().first()
                if not sm:
                    sm = StudentMastery(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        topic_id=topic_name,
                        mastery_percentage=t_score,
                        times_practiced=1,
                        consecutive_correct=1 if t_score >= 70.0 else 0,
                        last_evaluated_at=utc_now(),
                        weak_areas=[topic_name] if t_score < 60.0 else [],
                    )
                    self.db.add(sm)
                else:
                    sm.mastery_percentage = round((sm.mastery_percentage * 0.6) + (t_score * 0.4), 1)
                    sm.times_practiced += 1
                    sm.last_evaluated_at = utc_now()

        # Calculate Exam Readiness
        cfg_blueprint = (
            cfg.blueprint if (cfg and cfg.blueprint)
            else self.generator.get_default_blueprint(session.subject)
        )
        topic_masteries = {t["topic"]: t["score_percentage"] for t in topic_analysis}
        mock_stats = {
            "latest_score": score_pct,
            "unanswered_ratio": (unanswered_count / len(questions)) if questions else 0.0,
        }
        readiness_data = self.readiness_engine.compute_exam_readiness(
            blueprint=cfg_blueprint,
            topic_masteries=topic_masteries,
            mock_stats=mock_stats,
        )

        detailed_analysis = {
            "overall_score_percentage": score_pct,
            "marks_obtained": net_marks,
            "total_marks": session.total_marks,
            "negative_marks_deducted": round(total_deducted, 2),
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unanswered_count": unanswered_count,
            "topic_analysis": topic_analysis,
            "cognitive_diagnosis": cognitive_diagnosis,
            "remediation_action": remediation_action,
            "readiness": readiness_data,
        }

        session.status = "submitted"
        session.submitted_at = utc_now()
        session.marks_obtained = net_marks
        session.score_percentage = score_pct
        session.negative_marks_deducted = round(total_deducted, 2)
        session.answers_record = final_answers
        session.detailed_analysis = detailed_analysis

        if self.db:
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def get_readiness_analysis(self, user_id: str, config_id: Optional[str] = None) -> Dict[str, Any]:
        cfg = None
        if self.db and config_id:
            res = await self.db.execute(
                select(ExamConfig).where(ExamConfig.id == config_id, ExamConfig.user_id == user_id)
            )
            cfg = res.scalars().first()
        elif self.db:
            res = await self.db.execute(
                select(ExamConfig).where(ExamConfig.user_id == user_id)
            )
            cfg = res.scalars().first()

        subject = cfg.subject if cfg else "Operating Systems"
        blueprint = cfg.blueprint if (cfg and cfg.blueprint) else self.generator.get_default_blueprint(subject)

        # Gather masteries
        masteries: Dict[str, float] = {}
        if self.db:
            for topic in blueprint.keys():
                res = await self.db.execute(
                    select(StudentMastery).where(
                        StudentMastery.user_id == user_id,
                        StudentMastery.topic_id == topic
                    )
                )
                sm = res.scalars().first()
                if sm:
                    masteries[topic] = sm.mastery_percentage
                else:
                    masteries[topic] = 45.0
        else:
            masteries = {t: 50.0 for t in blueprint.keys()}

        # Gather recall stats
        recall_stats = {"total_items": 5, "due_items": 1}
        mock_stats = None

        if self.db:
            res_rev = await self.db.execute(
                select(RevisionItem).where(RevisionItem.user_id == user_id)
            )
            all_rev = list(res_rev.scalars().all())
            due_rev = [r for r in all_rev if r.is_due]
            recall_stats = {"total_items": len(all_rev), "due_items": len(due_rev)}

            res_mock = await self.db.execute(
                select(MockExamSession).where(
                    MockExamSession.user_id == user_id,
                    MockExamSession.status == "submitted"
                ).order_by(MockExamSession.submitted_at.desc())
            )
            latest_mock = res_mock.scalars().first()
            if latest_mock:
                mock_stats = {
                    "latest_score": latest_mock.score_percentage,
                    "unanswered_ratio": (latest_mock.detailed_analysis.get("unanswered_count", 0) / max(1, latest_mock.total_questions)),
                }

        readiness_res = self.readiness_engine.compute_exam_readiness(
            blueprint=blueprint,
            topic_masteries=masteries,
            recall_stats=recall_stats,
            mock_stats=mock_stats,
        )

        readiness_res["exam_title"] = cfg.title if cfg else f"{subject} Semester Exam"
        readiness_res["exam_date"] = cfg.exam_date.isoformat() if (cfg and cfg.exam_date) else None
        readiness_res["subject"] = subject
        return readiness_res

    def _is_answer_correct(self, question: Dict[str, Any], student_resp: str, correct_ans: str) -> bool:
        st = student_resp.lower().strip()
        ca = correct_ans.lower().strip()

        if st == ca:
            return True

        if question.get("question_type") == "multiple_select":
            expected_parts = [p.strip() for p in ca.split(",") if p.strip()]
            provided_parts = [p.strip() for p in st.split(",") if p.strip()]
            if expected_parts and all(any(ep in pp for pp in provided_parts) for ep in expected_parts):
                return True

        if question.get("question_type") in ["short_answer", "scenario", "coding"]:
            keywords = [k.strip() for k in ca.split() if len(k.strip()) > 3]
            matched = sum(1 for kw in keywords if kw in st)
            if keywords and (matched / len(keywords)) >= 0.5:
                return True

        return False

    def _generate_cognitive_diagnosis(
        self,
        topic_scores: List[Dict[str, Any]],
        misconceptions: List[Dict[str, Any]],
        unanswered_count: int,
        total_questions: int,
    ) -> Dict[str, Any]:
        deadlock_misconception = any(
            "prevention" in m.get("misconception_explanation", "").lower() or
            "avoidance" in m.get("misconception_explanation", "").lower()
            for m in misconceptions
        )
        weak_topics = [t["topic"] for t in topic_scores if t["tier"] in ["Weak", "Critical"]]

        if deadlock_misconception or any("deadlock" in wt.lower() for wt in weak_topics):
            core_issue = (
                "Your biggest problem isn't memorization. Your answers show confusion between "
                "deadlock prevention and deadlock avoidance."
            )
            deep_explanation = (
                "Deadlock Prevention operates statically by systematically eliminating one of the four "
                "necessary Coffman conditions (e.g. strict numerical resource ordering to prevent circular wait). "
                "In contrast, Deadlock Avoidance permits arbitrary resource requests at runtime, but uses dynamic "
                "lookahead algorithms (like Banker's Algorithm safe-state matrices) to postpone requests that would "
                "transition the system into an unsafe state."
            )
            key_remediation_concept = "Deadlock Prevention vs Avoidance"
        elif any("synchronization" in wt.lower() or "sync" in wt.lower() for wt in weak_topics):
            core_issue = (
                "Your primary hurdle is concurrency control semantics. "
                "You are conflating binary mutex locks with counting semaphore wait/post signaling."
            )
            deep_explanation = (
                "A mutex has strict ownership (only the thread that acquired the mutex can release it). "
                "A semaphore is an integer signal permit mechanism where any thread can signal sem_post() "
                "to unblock a waiting thread without ownership restrictions."
            )
            key_remediation_concept = "Counting Semaphores vs Mutexes"
        elif any("schedul" in wt.lower() for wt in weak_topics):
            core_issue = (
                "Your calculation logic shows confusion over CPU scheduling metrics, particularly "
                "between waiting time and turnaround time."
            )
            deep_explanation = (
                "Turnaround Time is the total interval from arrival to process termination (Completion - Arrival). "
                "Waiting Time is the time spent purely in the ready queue (Turnaround Time - Burst Time). "
                "In Shortest Job First (SJF), non-preemptive ordering minimizes waiting time, avoiding the convoy effect."
            )
            key_remediation_concept = "CPU Scheduling Waiting vs Turnaround Time"
        elif unanswered_count >= 3:
            core_issue = (
                f"Time management was your primary penalty: {unanswered_count} out of {total_questions} questions "
                "were left unanswered."
            )
            deep_explanation = (
                "Because negative marking only applies to incorrect answers (not blank ones), pacing yourself "
                "to attempt all high-confidence questions first will dramatically raise your net marks."
            )
            key_remediation_concept = "Exam Pacing & Time Allocation"
        else:
            core_issue = (
                "Your conceptual foundation is solid, but subtle edge-case distinctions cost marks."
            )
            deep_explanation = (
                "Review multi-condition architectural trade-offs to convert good theoretical knowledge "
                "into full marks on scenario questions."
            )
            key_remediation_concept = "Scenario Trade-off Analysis"

        return {
            "core_issue": core_issue,
            "deep_explanation": deep_explanation,
            "key_remediation_concept": key_remediation_concept,
            "detected_misconceptions_count": len(misconceptions),
            "unanswered_questions": unanswered_count,
        }
