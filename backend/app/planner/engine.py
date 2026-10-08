from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.learning import StudentMastery
from app.models.revision import RevisionItem
from app.models.planner import StudyPlan, StudyPlanItem


def utc_now():
    return datetime.now(timezone.utc)


def calculate_priority_score(
    mastery_gap: float,
    exam_weight: float,
    pyq_frequency: float,
    revision_urgency: float,
    exam_proximity: float,
    weakness_recurrence: float = 0.0,
    prerequisite_importance: float = 0.0,
) -> float:
    """
    Computes a weighted multidimensional priority score for competitive examination topics.
    Formula:
      0.25 * Mastery Gap +
      0.20 * Exam Weight +
      0.20 * PYQ Frequency +
      0.15 * Revision Urgency +
      0.10 * Exam Proximity +
      0.05 * Weakness Recurrence +
      0.05 * Prerequisite Importance
    Normalized on a 0.0 to 1.0 (or 0 to 100) scale.
    """
    raw_score = (
        0.25 * max(0.0, min(1.0, mastery_gap)) +
        0.20 * max(0.0, min(1.0, exam_weight)) +
        0.20 * max(0.0, min(1.0, pyq_frequency)) +
        0.15 * max(0.0, min(1.0, revision_urgency)) +
        0.10 * max(0.0, min(1.0, exam_proximity)) +
        0.05 * max(0.0, min(1.0, weakness_recurrence)) +
        0.05 * max(0.0, min(1.0, prerequisite_importance))
    )
    return round(raw_score * 100.0, 2)


class StudyPlannerEngine:
    """
    Core reasoning engine for dynamic study schedule synthesis,
    continuous re-planning, and micro-session optimization.
    Supports both AsyncSession DB storage and in-memory execution.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    async def create_plan(
        self,
        user_id: str,
        title: Optional[str] = None,
        subject: str = "Operating Systems",
        exam_date: Optional[datetime] = None,
        days_until_exam: int = 12,
        daily_study_minutes: int = 120,
        focus_weak_areas: bool = True,
    ) -> StudyPlan:
        """
        Synthesizes a brand new dynamic multi-phase study plan based on
        curriculum prerequisites, student mastery, spaced repetition queue, and exam blueprint.
        """
        if exam_date is None:
            exam_date = utc_now() + timedelta(days=days_until_exam)
        else:
            delta = (exam_date - utc_now()).days
            days_until_exam = max(1, delta)

        total_hours = (days_until_exam * daily_study_minutes) / 60.0
        plan_title = title or f"{subject} Exam Mastery Preparation Plan"

        # 1. Fetch student weak areas and existing mastery
        weak_topics = ["Deadlocks & Concurrency", "Process Synchronization"]
        mastery_map: Dict[str, float] = {"deadlocks & concurrency": 45.0, "process synchronization": 52.0}
        due_revision_count = 3

        if self.db:
            res = await self.db.execute(
                select(StudentMastery).where(StudentMastery.user_id == user_id)
            )
            masteries = list(res.scalars().all())
            if masteries:
                mastery_map = {m.topic_id.lower(): m.mastery_percentage for m in masteries}
                detected_weak = [m.topic_id for m in masteries if m.mastery_percentage < 65.0]
                if detected_weak:
                    weak_topics = detected_weak

            rev_res = await self.db.execute(
                select(RevisionItem).where(RevisionItem.user_id == user_id, RevisionItem.is_due.is_(True))
            )
            due_revision_count = len(list(rev_res.scalars().all()))

        # 2. Formulate phased strategy
        strategy = self._synthesize_phased_strategy(
            days_until_exam=days_until_exam,
            total_hours=total_hours,
            weak_topics=weak_topics,
            due_revision_count=due_revision_count,
        )

        plan = StudyPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=plan_title,
            subject=subject,
            exam_date=exam_date,
            daily_study_minutes=daily_study_minutes,
            total_days=days_until_exam,
            total_available_hours=total_hours,
            current_day=1,
            status="active",
            strategy_summary=strategy,
            last_replanned_at=utc_now(),
        )

        # 3. Populate daily scheduled session items across the days
        items = self._generate_schedule_items(
            plan_id=plan.id,
            days=days_until_exam,
            daily_minutes=daily_study_minutes,
            subject=subject,
            weak_topics=weak_topics,
            mastery_map=mastery_map,
        )
        plan.items = items

        if self.db:
            # Deactivate any previous active plan for same subject
            existing_res = await self.db.execute(
                select(StudyPlan).where(
                    StudyPlan.user_id == user_id,
                    StudyPlan.subject == subject,
                    StudyPlan.status == "active",
                )
            )
            for ep in existing_res.scalars().all():
                ep.status = "archived"

            self.db.add(plan)
            for item in items:
                self.db.add(item)
            await self.db.commit()
            await self.db.refresh(plan)

        return plan

    async def replan(
        self,
        plan_id: str,
        user_id: str,
        missed_days: int = 0,
        new_exam_date: Optional[datetime] = None,
        new_days_until_exam: Optional[int] = None,
        new_daily_study_minutes: Optional[int] = None,
        reason: str = "Missed study session / Date adjustment",
    ) -> StudyPlan:
        """
        Dynamically adjusts an existing plan without failing the student.
        Redistributes remaining essential tasks, recalculates density,
        and protects mock exam and weak area repair blocks.
        """
        plan = None
        if self.db:
            res = await self.db.execute(
                select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.user_id == user_id)
            )
            plan = res.scalars().first()

        if not plan:
            # Create a virtual plan if not found in db
            plan = await self.create_plan(user_id=user_id, days_until_exam=12, daily_study_minutes=120)

        # Determine new timeline
        current_day = plan.current_day + missed_days
        if new_days_until_exam is not None:
            remaining_days = max(1, new_days_until_exam)
            total_days = current_day + remaining_days - 1
            plan.total_days = total_days
            plan.exam_date = utc_now() + timedelta(days=remaining_days)
        elif new_exam_date is not None:
            plan.exam_date = new_exam_date
            remaining_days = max(1, (new_exam_date - utc_now()).days)
            plan.total_days = current_day + remaining_days - 1
        else:
            remaining_days = max(1, plan.total_days - current_day + 1)

        if new_daily_study_minutes is not None:
            plan.daily_study_minutes = new_daily_study_minutes

        plan.current_day = current_day
        plan.total_available_hours = (remaining_days * plan.daily_study_minutes) / 60.0
        plan.last_replanned_at = utc_now()

        weak_topics = ["Deadlocks & Concurrency", "Process Synchronization"]
        mastery_map: Dict[str, float] = {}

        if self.db:
            # Mark missed past items as skipped rather than failed
            items_res = await self.db.execute(
                select(StudyPlanItem).where(
                    StudyPlanItem.plan_id == plan.id,
                    StudyPlanItem.day_number < current_day,
                    StudyPlanItem.status == "pending",
                )
            )
            for pi in items_res.scalars().all():
                pi.status = "skipped"
                pi.notes = f"Auto-rescheduled on {utc_now().strftime('%b %d')}: {reason}"

            m_res = await self.db.execute(select(StudentMastery).where(StudentMastery.user_id == user_id))
            masteries = list(m_res.scalars().all())
            if masteries:
                weak_topics = [m.topic_id for m in masteries if m.mastery_percentage < 65.0] or weak_topics
                mastery_map = {m.topic_id.lower(): m.mastery_percentage for m in masteries}

            # Delete future pending items to rebuild an optimized remaining schedule
            await self.db.execute(
                delete(StudyPlanItem).where(
                    StudyPlanItem.plan_id == plan.id,
                    StudyPlanItem.day_number >= current_day,
                    StudyPlanItem.status == "pending",
                )
            )

        # Re-synthesize remaining schedule
        new_items = self._generate_schedule_items(
            plan_id=plan.id,
            days=remaining_days,
            daily_minutes=plan.daily_study_minutes,
            subject=plan.subject,
            weak_topics=weak_topics,
            mastery_map=mastery_map,
            start_day_number=current_day,
        )

        if self.db:
            for item in new_items:
                self.db.add(item)
            await self.db.commit()
            await self.db.refresh(plan)
        else:
            plan.items = new_items

        plan.strategy_summary = {
            "replan_reason": reason,
            "missed_days_absorbed": missed_days,
            "remaining_days": remaining_days,
            "remaining_hours": plan.total_available_hours,
            "rationale": (
                f"Absorbed {missed_days} missed day(s) gracefully. You have {remaining_days} days "
                f"({plan.total_available_hours:.1f} hours) left. We compressed secondary review and "
                f"preserved high-yield remediation on {', '.join(weak_topics[:2])} and final mock exams."
            ),
        }

        if self.db:
            await self.db.commit()
            await self.db.refresh(plan)

        return plan

    async def generate_micro_session(
        self,
        user_id: str,
        minutes: int = 30,
        subject: str = "Operating Systems",
    ) -> Dict[str, Any]:
        """
        Synthesizes a high-yield micro-session for immediate execution when the student
        has limited time (e.g. 15, 30, 45 minutes).
        """
        target_topic = "Deadlocks & Concurrency"

        if self.db:
            m_res = await self.db.execute(
                select(StudentMastery)
                .where(StudentMastery.user_id == user_id)
                .order_by(StudentMastery.mastery_percentage.asc())
            )
            weakest = m_res.scalars().first()
            if weakest:
                target_topic = weakest.topic_id

        if minutes <= 20:
            return {
                "allocated_minutes": minutes,
                "recommended_topic": target_topic,
                "session_type": "revision",
                "action_type": "active_recall",
                "action_payload": {
                    "mode": "quick_retrieval",
                    "duration_minutes": minutes,
                    "target_topic": target_topic,
                },
                "pedagogical_reasoning": (
                    f"With {minutes} minutes available, high-frequency active recall delivers "
                    f"the highest retention return per minute. Reviewing {target_topic}."
                ),
            }
        elif minutes <= 40:
            return {
                "allocated_minutes": minutes,
                "recommended_topic": target_topic,
                "session_type": "practice",
                "action_type": "practice_quiz",
                "action_payload": {
                    "topic": target_topic,
                    "subject": subject,
                    "question_count": 15,
                    "mode": "targeted_drill",
                },
                "pedagogical_reasoning": (
                    f"In this {minutes}-minute window, test your conceptual application on your "
                    f"weakest area ({target_topic}). 15 practice questions with instant Socratic feedback."
                ),
            }
        else:
            return {
                "allocated_minutes": minutes,
                "recommended_topic": target_topic,
                "session_type": "learn",
                "action_type": "socratic_lesson",
                "action_payload": {
                    "topic": target_topic,
                    "subject": subject,
                    "step_count": 3,
                },
                "pedagogical_reasoning": (
                    f"You have {minutes} minutes. Let us rebuild {target_topic} step-by-step "
                    f"with your Socratic Teacher beside you."
                ),
            }

    def _synthesize_phased_strategy(
        self,
        days_until_exam: int,
        total_hours: float,
        weak_topics: List[str],
        due_revision_count: int,
    ) -> Dict[str, Any]:
        phase1_days = max(1, int(days_until_exam * 0.35))
        phase2_days = max(1, int(days_until_exam * 0.35))
        phase3_days = max(1, int(days_until_exam * 0.15))
        phase4_days = max(1, days_until_exam - (phase1_days + phase2_days + phase3_days))

        return {
            "total_days": days_until_exam,
            "total_available_hours": total_hours,
            "high_yield_topics": weak_topics[:3],
            "due_spaced_retrievals": due_revision_count,
            "phases": [
                {
                    "phase_number": 1,
                    "name": "Core Concept Remediation & Gap Closing",
                    "days": f"Days 1–{phase1_days}",
                    "focus": f"Socratic mastery rebuilding on high-yield weak areas ({', '.join(weak_topics[:2])}).",
                },
                {
                    "phase_number": 2,
                    "name": "Interleaved Retrieval Practice",
                    "days": f"Days {phase1_days + 1}–{phase1_days + phase2_days}",
                    "focus": "20-question practice drills, active recall flashcard queue, and formula retention.",
                },
                {
                    "phase_number": 3,
                    "name": "Full Mock Exam Simulation",
                    "days": f"Days {phase1_days + phase2_days + 1}–{phase1_days + phase2_days + phase3_days}",
                    "focus": "Timed exam under strict negative marking to verify cognitive readiness.",
                },
                {
                    "phase_number": 4,
                    "name": "Weak Area Polish & Exam Readiness",
                    "days": f"Final {phase4_days} day(s)",
                    "focus": "Post-mock targeted error repair, high-priority summary notes, and confidence building.",
                },
            ],
            "rationale": (
                f"You have {total_hours:.1f} hours across {days_until_exam} days. We allocate "
                f"the first {phase1_days * 2} hours to rebuilding {weak_topics[0]}, then transition "
                f"to active retrieval, scheduled mock tests, and final polish."
            ),
        }

    def _generate_schedule_items(
        self,
        plan_id: str,
        days: int,
        daily_minutes: int,
        subject: str,
        weak_topics: List[str],
        mastery_map: Dict[str, float],
        start_day_number: int = 1,
    ) -> List[StudyPlanItem]:
        items: List[StudyPlanItem] = []
        curriculum_topics = [
            "Deadlocks & Concurrency",
            "Process Synchronization",
            "CPU Scheduling Algorithms",
            "Memory Management & Paging",
            "File Systems & I/O Protection",
        ]

        ordered_topics = []
        for wt in weak_topics:
            if wt in curriculum_topics and wt not in ordered_topics:
                ordered_topics.append(wt)
        for ct in curriculum_topics:
            if ct not in ordered_topics:
                ordered_topics.append(ct)

        for d_idx in range(days):
            day_num = start_day_number + d_idx
            scheduled_date = utc_now() + timedelta(days=d_idx)
            progress_ratio = (d_idx + 1) / max(1, days)

            if progress_ratio <= 0.40:
                topic = ordered_topics[d_idx % len(ordered_topics)]
                allocated = min(daily_minutes, 60)
                items.append(
                    StudyPlanItem(
                        id=str(uuid.uuid4()),
                        plan_id=plan_id,
                        day_number=day_num,
                        scheduled_date=scheduled_date,
                        session_type="learn",
                        topic=topic,
                        allocated_minutes=allocated,
                        priority_weight=0.9,
                        status="pending",
                        action_type="socratic_lesson",
                        action_payload={"topic": topic, "subject": subject},
                    )
                )

                if daily_minutes > 60:
                    items.append(
                        StudyPlanItem(
                            id=str(uuid.uuid4()),
                            plan_id=plan_id,
                            day_number=day_num,
                            scheduled_date=scheduled_date,
                            session_type="revision",
                            topic=topic,
                            allocated_minutes=daily_minutes - allocated,
                            priority_weight=0.8,
                            status="pending",
                            action_type="active_recall",
                            action_payload={"topic": topic, "subject": subject},
                        )
                    )

            elif progress_ratio <= 0.75:
                topic = ordered_topics[(d_idx - 1) % len(ordered_topics)]
                allocated = min(daily_minutes, 60)
                items.append(
                    StudyPlanItem(
                        id=str(uuid.uuid4()),
                        plan_id=plan_id,
                        day_number=day_num,
                        scheduled_date=scheduled_date,
                        session_type="practice",
                        topic=topic,
                        allocated_minutes=allocated,
                        priority_weight=0.85,
                        status="pending",
                        action_type="practice_quiz",
                        action_payload={"topic": topic, "subject": subject, "question_count": 20},
                    )
                )

                if daily_minutes > 60:
                    items.append(
                        StudyPlanItem(
                            id=str(uuid.uuid4()),
                            plan_id=plan_id,
                            day_number=day_num,
                            scheduled_date=scheduled_date,
                            session_type="revision",
                            topic="Spaced Repetition Active Recall Queue",
                            allocated_minutes=daily_minutes - allocated,
                            priority_weight=0.75,
                            status="pending",
                            action_type="active_recall",
                            action_payload={"subject": subject},
                        )
                    )

            elif progress_ratio <= 0.90:
                items.append(
                    StudyPlanItem(
                        id=str(uuid.uuid4()),
                        plan_id=plan_id,
                        day_number=day_num,
                        scheduled_date=scheduled_date,
                        session_type="mock_exam",
                        topic=f"{subject} Full Mock Examination",
                        allocated_minutes=min(daily_minutes, 90),
                        priority_weight=0.95,
                        status="pending",
                        action_type="mock_exam",
                        action_payload={"subject": subject, "duration_minutes": 60, "total_marks": 100},
                    )
                )

            else:
                primary_weak = weak_topics[0] if weak_topics else "Deadlocks & Concurrency"
                items.append(
                    StudyPlanItem(
                        id=str(uuid.uuid4()),
                        plan_id=plan_id,
                        day_number=day_num,
                        scheduled_date=scheduled_date,
                        session_type="weak_repair",
                        topic=f"Exam Polish & Weak Area Fix ({primary_weak})",
                        allocated_minutes=daily_minutes,
                        priority_weight=1.0,
                        status="pending",
                        action_type="socratic_lesson",
                        action_payload={"topic": primary_weak, "subject": subject, "mode": "rapid_remediation"},
                    )
                )

        return items

    async def create_competitive_exam_plan(
        self,
        user_id: str,
        exam_code: str = "upsc_cse",
        target_year: int = 2026,
        days_until_exam: int = 60,
        daily_study_minutes: int = 360,
        stage: str = "prelims_cum_mains",
        optional_subject: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> StudyPlan:
        """
        Synthesizes a structured multi-slot competitive examination plan.
        Partitions daily study time across:
          - Core Syllabus / Static Concepts (40%)
          - Current Affairs & Static Linking (20%)
          - PYQ & Test Series Practice (25%)
          - Answer Writing / Spaced Revision (15%)
        """
        exam_title = f"{exam_code.upper().replace('_', ' ')} {target_year} Strategic Mastery Plan"
        exam_date = utc_now() + timedelta(days=days_until_exam)
        total_hours = (days_until_exam * daily_study_minutes) / 60.0

        topics = focus_areas or [
            "Indian Polity & Governance",
            "Modern Indian History & Freedom Struggle",
            "Geography & Environment",
            "Indian Economy & Development",
            "General Science & Tech",
            "Ethics, Integrity & Aptitude",
        ]

        strategy_summary = {
            "exam_code": exam_code,
            "target_year": target_year,
            "stage": stage,
            "optional_subject": optional_subject,
            "daily_time_allocation": {
                "static_core_minutes": int(daily_study_minutes * 0.40),
                "current_affairs_minutes": int(daily_study_minutes * 0.20),
                "pyq_practice_minutes": int(daily_study_minutes * 0.25),
                "answer_writing_revision_minutes": int(daily_study_minutes * 0.15),
            },
            "phases": [
                {"name": "Foundation & Syllabus Coverage", "duration_pct": 50},
                {"name": "Intensive PYQ & Revision Consolidation", "duration_pct": 30},
                {"name": "Full-Length Mocks & High-Yield Polish", "duration_pct": 20},
            ],
        }

        plan = StudyPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=exam_title,
            subject=exam_code.upper().replace("_", " "),
            exam_date=exam_date,
            daily_study_minutes=daily_study_minutes,
            total_days=days_until_exam,
            total_available_hours=total_hours,
            current_day=1,
            status="active",
            strategy_summary=strategy_summary,
            last_replanned_at=utc_now(),
        )

        items: List[StudyPlanItem] = []
        static_mins = int(daily_study_minutes * 0.40)
        ca_mins = int(daily_study_minutes * 0.20)
        pyq_mins = int(daily_study_minutes * 0.25)
        mains_mins = daily_study_minutes - (static_mins + ca_mins + pyq_mins)

        # Generate up to 14 days or days_until_exam items
        schedule_days = min(days_until_exam, 14)
        for day_num in range(1, schedule_days + 1):
            scheduled_date = utc_now() + timedelta(days=day_num - 1)
            topic = topics[(day_num - 1) % len(topics)]

            # Slot 1: Static GS Core
            items.append(
                StudyPlanItem(
                    id=str(uuid.uuid4()),
                    plan_id=plan.id,
                    day_number=day_num,
                    scheduled_date=scheduled_date,
                    session_type="learn",
                    topic=f"{topic} (Static Core)",
                    allocated_minutes=static_mins,
                    priority_weight=0.9,
                    status="pending",
                    action_type="socratic_lesson",
                    action_payload={"exam_code": exam_code, "topic": topic, "stage": stage},
                )
            )

            # Slot 2: Current Affairs & Static Linking
            items.append(
                StudyPlanItem(
                    id=str(uuid.uuid4()),
                    plan_id=plan.id,
                    day_number=day_num,
                    scheduled_date=scheduled_date,
                    session_type="current_affairs",
                    topic="Daily Current Affairs & Static Concept Linking",
                    allocated_minutes=ca_mins,
                    priority_weight=0.85,
                    status="pending",
                    action_type="current_affairs_feed",
                    action_payload={"exam_code": exam_code, "date": scheduled_date.strftime("%Y-%m-%d")},
                )
            )

            # Slot 3: PYQ Practice / CSAT
            pyq_session_topic = f"{topic} PYQ Practice" if day_num % 3 != 0 else "CSAT Aptitude & Comprehension"
            items.append(
                StudyPlanItem(
                    id=str(uuid.uuid4()),
                    plan_id=plan.id,
                    day_number=day_num,
                    scheduled_date=scheduled_date,
                    session_type="practice",
                    topic=pyq_session_topic,
                    allocated_minutes=pyq_mins,
                    priority_weight=0.85,
                    status="pending",
                    action_type="pyq_practice",
                    action_payload={"exam_code": exam_code, "topic": topic, "count": 15},
                )
            )

            # Slot 4: Mains Answer Writing / Spaced Revision
            items.append(
                StudyPlanItem(
                    id=str(uuid.uuid4()),
                    plan_id=plan.id,
                    day_number=day_num,
                    scheduled_date=scheduled_date,
                    session_type="revision",
                    topic="Mains Answer Writing & Active Recall",
                    allocated_minutes=mains_mins,
                    priority_weight=0.8,
                    status="pending",
                    action_type="answer_writing",
                    action_payload={"exam_code": exam_code, "topic": topic, "questions": 2},
                )
            )

        plan.schedule_items = items

        if self.db:
            self.db.add(plan)
            for it in items:
                self.db.add(it)
            await self.db.commit()
            await self.db.refresh(plan)

        return plan
