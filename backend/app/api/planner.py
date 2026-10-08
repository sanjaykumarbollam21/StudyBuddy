from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.models.planner import StudyPlan, StudyPlanItem
from app.planner.engine import StudyPlannerEngine
from app.planner.agent import StudyAgentService
from app.schemas.planner import (
    StudyPlanCreateRequest,
    StudyPlanResponse,
    StudyPlanItemResponse,
    ReplanRequest,
    MicroSessionResponse,
    AgentChatRequest,
    AgentChatResponse,
)

router = APIRouter(prefix="/planner", tags=["Intelligent Study Planner & AI Study Agent"])


@router.post("/plans", response_model=StudyPlanResponse)
async def create_or_initialize_study_plan(
    request: StudyPlanCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a dynamic, multi-phase study plan balancing curriculum prerequisites,
    mastery gaps, spaced repetition queue, and exam blueprint.
    """
    try:
        engine = StudyPlannerEngine(db)
        plan = await engine.create_plan(
            user_id=current_user.id,
            title=request.title,
            subject=request.subject,
            exam_date=request.exam_date,
            days_until_exam=request.days_until_exam or 12,
            daily_study_minutes=request.daily_study_minutes,
            focus_weak_areas=request.focus_weak_areas,
        )

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in plan.items
            if item.day_number == plan.current_day
        ]
        all_items = [StudyPlanItemResponse.model_validate(item) for item in plan.items]

        completed = sum(1 for it in plan.items if it.status == "completed")
        progress = (completed / max(1, len(plan.items))) * 100.0

        return StudyPlanResponse(
            id=plan.id,
            title=plan.title,
            subject=plan.subject,
            exam_date=plan.exam_date,
            daily_study_minutes=plan.daily_study_minutes,
            total_days=plan.total_days,
            total_available_hours=plan.total_available_hours,
            current_day=plan.current_day,
            status=plan.status,
            strategy_summary=plan.strategy_summary,
            last_replanned_at=plan.last_replanned_at,
            items=all_items,
            today_items=today_items,
            progress_percentage=progress,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create study plan: {str(e)}",
        )


@router.get("/plans/active", response_model=StudyPlanResponse)
async def get_active_study_plan(
    subject: str = Query("Operating Systems"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves student's active plan, today's actionable session blocks,
    and long-term phase trajectories. If none exists, creates a fresh default plan.
    """
    try:
        res = await db.execute(
            select(StudyPlan)
            .where(
                StudyPlan.user_id == current_user.id,
                StudyPlan.subject.ilike(f"%{subject}%"),
                StudyPlan.status == "active",
            )
        )
        plan = res.scalars().first()

        engine = StudyPlannerEngine(db)
        if not plan:
            plan = await engine.create_plan(
                user_id=current_user.id,
                subject=subject,
                days_until_exam=12,
                daily_study_minutes=120,
            )

        # Refresh items
        items_res = await db.execute(
            select(StudyPlanItem)
            .where(StudyPlanItem.plan_id == plan.id)
            .order_by(StudyPlanItem.day_number.asc())
        )
        items = list(items_res.scalars().all())

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in items
            if item.day_number == plan.current_day
        ]
        all_items = [StudyPlanItemResponse.model_validate(item) for item in items]

        completed = sum(1 for it in items if it.status == "completed")
        progress = (completed / max(1, len(items))) * 100.0

        return StudyPlanResponse(
            id=plan.id,
            title=plan.title,
            subject=plan.subject,
            exam_date=plan.exam_date,
            daily_study_minutes=plan.daily_study_minutes,
            total_days=plan.total_days,
            total_available_hours=plan.total_available_hours,
            current_day=plan.current_day,
            status=plan.status,
            strategy_summary=plan.strategy_summary,
            last_replanned_at=plan.last_replanned_at,
            items=all_items,
            today_items=today_items,
            progress_percentage=progress,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch active study plan: {str(e)}",
        )


@router.post("/replan", response_model=StudyPlanResponse)
async def replan_study_schedule(
    request: ReplanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Dynamically recalculates the remaining plan when the student misses sessions
    or adjusts exam dates, without failing or penalizing the student.
    """
    try:
        res = await db.execute(
            select(StudyPlan)
            .where(StudyPlan.user_id == current_user.id, StudyPlan.status == "active")
        )
        plan = res.scalars().first()
        if not plan:
            raise HTTPException(status_code=404, detail="No active plan to replan.")

        engine = StudyPlannerEngine(db)
        updated_plan = await engine.replan(
            plan_id=plan.id,
            user_id=current_user.id,
            missed_days=request.missed_days or 0,
            new_exam_date=request.new_exam_date,
            new_days_until_exam=request.new_days_until_exam,
            new_daily_study_minutes=request.new_daily_study_minutes,
            reason=request.reason or "Dynamic re-plan requested",
        )

        items_res = await db.execute(
            select(StudyPlanItem)
            .where(StudyPlanItem.plan_id == updated_plan.id)
            .order_by(StudyPlanItem.day_number.asc())
        )
        items = list(items_res.scalars().all())

        today_items = [
            StudyPlanItemResponse.model_validate(item)
            for item in items
            if item.day_number == updated_plan.current_day
        ]
        all_items = [StudyPlanItemResponse.model_validate(item) for item in items]
        completed = sum(1 for it in items if it.status == "completed")
        progress = (completed / max(1, len(items))) * 100.0

        return StudyPlanResponse(
            id=updated_plan.id,
            title=updated_plan.title,
            subject=updated_plan.subject,
            exam_date=updated_plan.exam_date,
            daily_study_minutes=updated_plan.daily_study_minutes,
            total_days=updated_plan.total_days,
            total_available_hours=updated_plan.total_available_hours,
            current_day=updated_plan.current_day,
            status=updated_plan.status,
            strategy_summary=updated_plan.strategy_summary,
            last_replanned_at=updated_plan.last_replanned_at,
            items=all_items,
            today_items=today_items,
            progress_percentage=progress,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to replan study schedule: {str(e)}",
        )


@router.get("/micro-session", response_model=MicroSessionResponse)
async def get_micro_session(
    minutes: int = Query(30, ge=10, le=180),
    subject: str = Query("Operating Systems"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a high-yield micro-session for immediate study when student has limited time.
    """
    try:
        engine = StudyPlannerEngine(db)
        micro = await engine.generate_micro_session(
            user_id=current_user.id,
            minutes=minutes,
            subject=subject,
        )
        return MicroSessionResponse(
            allocated_minutes=micro["allocated_minutes"],
            recommended_topic=micro["recommended_topic"],
            session_type=micro["session_type"],
            action_type=micro["action_type"],
            action_payload=micro["action_payload"],
            pedagogical_reasoning=micro["pedagogical_reasoning"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate micro-session: {str(e)}",
        )


@router.post("/agent/chat", response_model=AgentChatResponse)
async def chat_with_study_agent(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Conversational agent task layer:
    Interprets natural language goals ("What should I study now?", "I have 30 minutes",
    "I missed yesterday", "Move my exam to next Monday") and routes directly to learning actions.
    """
    try:
        agent = StudyAgentService(db)
        return await agent.process_student_message(
            user_id=current_user.id,
            message=request.message,
            plan_id=request.plan_id,
            context_minutes=request.context_minutes,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process study agent request: {str(e)}",
        )


@router.post("/items/{item_id}/complete")
async def mark_study_item_completed(
    item_id: str,
    performance_score: Optional[float] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks a scheduled study block as completed and records performance score.
    """
    try:
        res = await db.execute(select(StudyPlanItem).where(StudyPlanItem.id == item_id))
        item = res.scalars().first()
        if not item:
            raise HTTPException(status_code=404, detail="Study plan item not found.")

        item.status = "completed"
        item.completed_at = utc_now()
        if performance_score is not None:
            item.performance_score = performance_score

        await db.commit()
        return {"success": True, "item_id": item_id, "status": "completed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete study plan item: {str(e)}",
        )
