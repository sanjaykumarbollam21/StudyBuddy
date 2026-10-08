from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.revision.service import RevisionService
from app.schemas.revision import (
    RevisionItemResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    DailyAgendaResponse,
)

router = APIRouter(prefix="/revision", tags=["Spaced Repetition & Intelligent Revision"])


@router.get("/due", response_model=List[RevisionItemResponse])
async def get_due_revision_items(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches prioritized active recall concepts due for spaced repetition review.
    Prioritizes weak concepts and overdue items.
    """
    try:
        service = RevisionService(db)
        return await service.get_due_reviews(user_id=current_user.id, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch due revision items: {str(e)}",
        )


@router.post("/submit", response_model=SubmitReviewResponse)
async def submit_active_recall_review(
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Processes an active recall review with the SM-2 algorithm, updates the next review date,
    recalculates multi-factor hardened mastery, and logs remediation if retention lapsed.
    """
    try:
        service = RevisionService(db)
        result = await service.submit_review(
            user_id=current_user.id,
            item_id=request.item_id,
            quality_rating=request.quality_rating,
            student_recall=request.student_recall,
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process revision review: {str(e)}",
        )


@router.get("/agenda", response_model=DailyAgendaResponse)
async def get_daily_learning_agenda(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Synthesizes 'Today's Learning' Hub for the dashboard:
    Roadmap milestone, due reviews, weak area alerts, and exam priorities.
    """
    try:
        service = RevisionService(db)
        return await service.get_daily_agenda(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily learning agenda: {str(e)}",
        )
