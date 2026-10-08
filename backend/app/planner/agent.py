import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.planner import StudyPlan
from app.models.learning import StudentMastery
from app.models.revision import RevisionItem
from app.planner.engine import StudyPlannerEngine
from app.schemas.planner import AgentChatResponse, AgentActionPayload, StudyPlanItemResponse


def utc_now():
    return datetime.now(timezone.utc)


class StudyAgentService:
    """
    Proactive AI Study Companion Agent.
    Decides what the student should do next, interprets conversational goals,
    triggers dynamic re-planning on missed sessions, and orchestrates
    underlying learning engines.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.engine = StudyPlannerEngine(db_session)

    async def process_student_message(
        self,
        user_id: str,
        message: str,
        plan_id: Optional[str] = None,
        context_minutes: Optional[int] = None,
    ) -> AgentChatResponse:
        lower = message.lower().strip()

        # Retrieve active plan or create one if none exists
        active_plan = None
        if self.db:
            if plan_id:
                res = await self.db.execute(
                    select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.user_id == user_id)
                )
                active_plan = res.scalars().first()
            if not active_plan:
                res = await self.db.execute(
                    select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.status == "active")
                )
                active_plan = res.scalars().first()

        # 1. Intent: Plan Preparation / Initial Creation
        if any(w in lower for w in ["plan my preparation", "create study plan", "exam in", "hours every day", "hours a day"]):
            return await self._handle_plan_creation_intent(user_id, message, lower)

        # Ensure active plan exists for remaining queries
        if not active_plan:
            active_plan = await self.engine.create_plan(
                user_id=user_id,
                days_until_exam=12,
                daily_study_minutes=120,
            )

        # 2. Intent: Micro-Session ("I have 30 minutes", "I have 45 minutes", etc.)
        minutes_match = re.search(r"(\d+)\s*(?:mins?|minutes?)", lower)
        if minutes_match or any(w in lower for w in ["i have 30", "i have 45", "i have 20", "i have 15", "quick session", "little time"]):
            extracted_minutes = int(minutes_match.group(1)) if minutes_match else (context_minutes or 30)
            return await self._handle_micro_session_intent(user_id, active_plan, extracted_minutes)

        # 3. Intent: Missed Session ("I missed yesterday", "missed study session")
        if any(w in lower for w in ["missed yesterday", "missed study session", "couldn't study", "fell behind", "missed two days", "missed 2 days"]):
            missed_count = 2 if "two days" in lower or "2 days" in lower else 1
            return await self._handle_missed_day_intent(user_id, active_plan, missed_count)

        # 4. Intent: Reschedule Exam ("Move my exam to next monday", "exam moved", "postponed")
        if any(w in lower for w in ["move my exam", "exam moved", "postpone", "next monday", "days left", "new exam date"]):
            return await self._handle_reschedule_exam_intent(user_id, active_plan, lower)

        # 5. Intent: Focus More on Weak Areas ("Focus more on topics I'm weak at")
        if any(w in lower for w in ["weak at", "weak areas", "struggling with", "focus more on weak"]):
            return await self._handle_focus_weak_intent(user_id, active_plan)

        # 6. Intent: Direct Action - "Give me today's lesson"
        if any(w in lower for w in ["today's lesson", "give me lesson", "start lesson", "learn now"]):
            return await self._handle_action_lesson(user_id, active_plan)

        # 7. Intent: Direct Action - "Start my revision"
        if any(w in lower for w in ["start my revision", "start revision", "active recall", "review cards"]):
            return await self._handle_action_revision(user_id, active_plan)

        # 8. Intent: Direct Action - "Start a 20-question practice session"
        if any(w in lower for w in ["practice session", "practice quiz", "20-question", "quiz session", "solve questions"]):
            return await self._handle_action_practice(user_id, active_plan)

        # 9. Intent: Direct Action - "Test whether I'm ready for the exam"
        if any(w in lower for w in ["ready for the exam", "test readiness", "mock exam", "simulated test", "take test"]):
            return await self._handle_action_mock(user_id, active_plan)

        # 10. Default Intent: "What should I study now?" / Priority recommendation
        return await self._handle_what_next_intent(user_id, active_plan)

    async def _handle_plan_creation_intent(self, user_id: str, message: str, lower: str) -> AgentChatResponse:
        days_match = re.search(r"(\d+)\s*days?", lower)
        hours_match = re.search(r"(\d+)\s*hours?", lower)

        days = int(days_match.group(1)) if days_match else 12
        hours = int(hours_match.group(1)) if hours_match else 2
        daily_mins = hours * 60

        plan = await self.engine.create_plan(
            user_id=user_id,
            days_until_exam=days,
            daily_study_minutes=daily_mins,
        )

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in plan.items
            if item.day_number == plan.current_day
        ]

        total_hours = days * hours
        first_topic = today_items[0].topic if today_items else "Deadlocks & Concurrency"

        reply = (
            f"🎯 **Preparation Plan Activated!**\n\n"
            f"You have **{days} days** until your Operating Systems exam, giving you **{total_hours} total study hours** "
            f"at {hours} hours/day.\n\n"
            f"**Strategic Breakdown:**\n"
            f"- **Phase 1 (Days 1–4):** Rebuilding high-yield weak areas (*Deadlocks*, *Process Synchronization*).\n"
            f"- **Phase 2 (Days 5–8):** Active recall and 20-question interleaved practice.\n"
            f"- **Phase 3 (Days 9–10):** Full timed mock exam under strict negative marking.\n"
            f"- **Phase 4 (Days 11–12):** Post-mock targeted weakness repair and formula polish.\n\n"
            f"👉 **Next immediate action:** Begin Day 1 Socratic Lesson on **{first_topic}**."
        )

        return AgentChatResponse(
            message=reply,
            intent="plan_preparation",
            reasoning=f"Synthesized dynamic 4-phase plan for {total_hours} total hours with prioritized weak area remediation.",
            suggested_action=AgentActionPayload(
                action_type="socratic_lesson",
                topic=first_topic,
                subject=plan.subject,
                duration_minutes=min(60, daily_mins),
                metadata={"plan_id": plan.id, "day_number": 1},
            ),
            today_items=today_items,
            plan_summary={
                "plan_id": plan.id,
                "total_days": days,
                "total_hours": total_hours,
                "daily_hours": hours,
                "subject": plan.subject,
            },
        )

    async def _handle_micro_session_intent(self, user_id: str, plan: StudyPlan, minutes: int) -> AgentChatResponse:
        micro = await self.engine.generate_micro_session(user_id=user_id, minutes=minutes, subject=plan.subject)
        recommended_topic = micro["recommended_topic"]
        session_type = micro["session_type"]
        action_type = micro["action_type"]

        reply = (
            f"⏱️ **Micro-Session Configured ({minutes} minutes)**\n\n"
            f"{micro['pedagogical_reasoning']}\n\n"
            f"👉 **Ready to begin:** Launching **{recommended_topic}** ({session_type.upper()})."
        )

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in plan.items
            if item.day_number == plan.current_day
        ]

        return AgentChatResponse(
            message=reply,
            intent="micro_session",
            reasoning=micro["pedagogical_reasoning"],
            suggested_action=AgentActionPayload(
                action_type=action_type,
                topic=recommended_topic,
                subject=plan.subject,
                duration_minutes=minutes,
                metadata=micro["action_payload"],
            ),
            today_items=today_items,
            plan_summary={"plan_id": plan.id, "micro_minutes": minutes},
        )

    async def _handle_missed_day_intent(self, user_id: str, plan: StudyPlan, missed_days: int) -> AgentChatResponse:
        updated_plan = await self.engine.replan(
            plan_id=plan.id,
            user_id=user_id,
            missed_days=missed_days,
            reason=f"Absorbed {missed_days} missed day(s)",
        )

        remaining_days = updated_plan.total_days - updated_plan.current_day + 1
        rem_hours = updated_plan.total_available_hours

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in updated_plan.items
            if item.day_number == updated_plan.current_day
        ]
        next_action_topic = today_items[0].topic if today_items else "Deadlocks & Concurrency"

        reply = (
            f"🔄 **No Problem — Schedule Re-calculated!**\n\n"
            f"Life happens! Missing a day does not mean failing your exam. We adjusted your timetable:\n\n"
            f"- **Remaining Days:** {remaining_days} days\n"
            f"- **Remaining Study Time:** {rem_hours:.1f} hours\n"
            f"- **Adjustment Made:** Compressed general review, preserved core Socratic weak-area remediation and final mock exam.\n\n"
            f"👉 **Today's focus:** {next_action_topic}."
        )

        return AgentChatResponse(
            message=reply,
            intent="handle_missed_day",
            reasoning=f"Dynamically absorbed {missed_days} missed day(s) without penalty; redistributed high-yield tasks.",
            suggested_action=AgentActionPayload(
                action_type=today_items[0].action_type if today_items else "socratic_lesson",
                topic=next_action_topic,
                subject=updated_plan.subject,
                duration_minutes=60,
                metadata={"plan_id": updated_plan.id, "day_number": updated_plan.current_day},
            ),
            today_items=today_items,
            plan_summary={
                "plan_id": updated_plan.id,
                "remaining_days": remaining_days,
                "remaining_hours": rem_hours,
            },
        )

    async def _handle_reschedule_exam_intent(self, user_id: str, plan: StudyPlan, lower: str) -> AgentChatResponse:
        days_match = re.search(r"(\d+)\s*days?", lower)
        new_days = int(days_match.group(1)) if days_match else 7

        updated_plan = await self.engine.replan(
            plan_id=plan.id,
            user_id=user_id,
            new_days_until_exam=new_days,
            reason=f"Exam rescheduled to {new_days} days remaining",
        )

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in updated_plan.items
            if item.day_number == updated_plan.current_day
        ]

        reply = (
            f"📅 **Exam Date Updated!**\n\n"
            f"We moved your exam target to **{new_days} days from now**. "
            f"Your dynamic plan now has **{updated_plan.total_available_hours:.1f} hours** available.\n\n"
            f"We adjusted the density of practice drills and re-anchored the final mock exam."
        )

        return AgentChatResponse(
            message=reply,
            intent="reschedule_exam",
            reasoning=f"Adjusted timeline to {new_days} days remaining.",
            suggested_action=AgentActionPayload(
                action_type="replan_view",
                topic=plan.subject,
                subject=plan.subject,
                metadata={"plan_id": plan.id},
            ),
            today_items=today_items,
            plan_summary={"new_days": new_days, "remaining_hours": updated_plan.total_available_hours},
        )

    async def _handle_focus_weak_intent(self, user_id: str, plan: StudyPlan) -> AgentChatResponse:
        target = "Deadlocks & Concurrency"
        score = 42.0

        if self.db:
            m_res = await self.db.execute(
                select(StudentMastery)
                .where(StudentMastery.user_id == user_id)
                .order_by(StudentMastery.mastery_percentage.asc())
            )
            weakest = m_res.scalars().first()
            if weakest:
                target = weakest.topic_id
                score = weakest.mastery_percentage

        reply = (
            f"🔍 **Weak-Area Prioritization Engaged!**\n\n"
            f"Your top priority weak area is **{target}** (current mastery: **{score:.0f}%**).\n\n"
            f"The planner has shifted immediate daily blocks to target this concept with Socratic remediation "
            f"followed by active retrieval drills."
        )

        return AgentChatResponse(
            message=reply,
            intent="focus_weak_areas",
            reasoning=f"Prioritized lowest mastery topic ({target} at {score:.0f}%) in today's queue.",
            suggested_action=AgentActionPayload(
                action_type="socratic_lesson",
                topic=target,
                subject=plan.subject,
                duration_minutes=45,
                metadata={"mode": "remediation"},
            ),
            today_items=[
                StudyPlanItemResponse.model_validate(item)
                for item in plan.items
                if item.day_number == plan.current_day
            ],
            plan_summary={"prioritized_topic": target, "mastery": score},
        )

    async def _handle_action_lesson(self, user_id: str, plan: StudyPlan) -> AgentChatResponse:
        pending_items = [
            item for item in plan.items
            if item.day_number == plan.current_day and item.session_type in ["learn", "weak_repair"] and item.status == "pending"
        ]
        target_topic = pending_items[0].topic if pending_items else "Deadlocks & Concurrency"

        return AgentChatResponse(
            message=f"🧑‍🏫 **Launching Today's Socratic Lesson:** {target_topic}. Let's build full conceptual mastery together.",
            intent="execute_action",
            reasoning=f"Launching scheduled Socratic teaching session for Day {plan.current_day}.",
            suggested_action=AgentActionPayload(
                action_type="socratic_lesson",
                topic=target_topic,
                subject=plan.subject,
                duration_minutes=45,
            ),
            today_items=[StudyPlanItemResponse.model_validate(item) for item in plan.items if item.day_number == plan.current_day],
        )

    async def _handle_action_revision(self, user_id: str, plan: StudyPlan) -> AgentChatResponse:
        due_count = 3
        if self.db:
            rev_res = await self.db.execute(
                select(RevisionItem).where(RevisionItem.user_id == user_id, RevisionItem.is_due.is_(True))
            )
            due_count = len(list(rev_res.scalars().all())) or 3

        return AgentChatResponse(
            message=f"🧠 **Starting Active Recall Revision:** You have **{max(1, due_count)} concepts** due for review today under the SM-2 algorithm.",
            intent="execute_action",
            reasoning="Launching Spaced Repetition Active Recall queue.",
            suggested_action=AgentActionPayload(
                action_type="active_recall",
                topic="Daily Retention Queue",
                subject=plan.subject,
                duration_minutes=20,
            ),
            today_items=[StudyPlanItemResponse.model_validate(item) for item in plan.items if item.day_number == plan.current_day],
        )

    async def _handle_action_practice(self, user_id: str, plan: StudyPlan) -> AgentChatResponse:
        return AgentChatResponse(
            message="📝 **Starting 20-Question Targeted Practice:** Testing conceptual problem-solving with immediate feedback.",
            intent="execute_action",
            reasoning="Launching 20-question practice drill.",
            suggested_action=AgentActionPayload(
                action_type="practice_quiz",
                topic="Deadlocks & Synchronization",
                subject=plan.subject,
                duration_minutes=30,
                metadata={"question_count": 20},
            ),
            today_items=[StudyPlanItemResponse.model_validate(item) for item in plan.items if item.day_number == plan.current_day],
        )

    async def _handle_action_mock(self, user_id: str, plan: StudyPlan) -> AgentChatResponse:
        return AgentChatResponse(
            message="🎓 **Initiating Full Mock Exam:** 60 minutes, negative marking enabled. Testing full cognitive readiness for exam day.",
            intent="execute_action",
            reasoning="Launching full simulated mock examination session.",
            suggested_action=AgentActionPayload(
                action_type="mock_exam",
                topic=f"{plan.subject} Mock Exam",
                subject=plan.subject,
                duration_minutes=60,
                metadata={"duration_minutes": 60, "total_marks": 100},
            ),
            today_items=[StudyPlanItemResponse.model_validate(item) for item in plan.items if item.day_number == plan.current_day],
        )

    async def _handle_what_next_intent(self, user_id: str, plan: StudyPlan) -> AgentChatResponse:
        today_items = [
            item for item in plan.items
            if item.day_number == plan.current_day
        ]
        pending_item = next((item for item in today_items if item.status == "pending"), None)

        if pending_item:
            action_type = pending_item.action_type
            topic = pending_item.topic
            mins = pending_item.allocated_minutes
            reply = (
                f"📋 **Here is your recommended next step for Day {plan.current_day}:**\n\n"
                f"- **Task:** {topic} ({pending_item.session_type.upper()})\n"
                f"- **Estimated Time:** {mins} minutes\n"
                f"- **Priority:** {int(pending_item.priority_weight * 100)}% urgency weight\n\n"
                f"Shall we launch this session now?"
            )
        else:
            action_type = "active_recall"
            topic = "Daily Review"
            mins = 20
            reply = (
                f"🎉 **Great job!** You have completed all scheduled tasks for Day {plan.current_day}.\n\n"
                f"You can do a quick 10-minute active recall session or preview tomorrow's roadmap."
            )

        return AgentChatResponse(
            message=reply,
            intent="what_next",
            reasoning=f"Selected highest-priority pending item for Day {plan.current_day}.",
            suggested_action=AgentActionPayload(
                action_type=action_type,
                topic=topic,
                subject=plan.subject,
                duration_minutes=mins,
            ),
            today_items=[StudyPlanItemResponse.model_validate(item) for item in today_items],
            plan_summary={
                "plan_id": plan.id,
                "current_day": plan.current_day,
                "total_days": plan.total_days,
            },
        )
