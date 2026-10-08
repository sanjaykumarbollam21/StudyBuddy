from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.practice.service import PracticeService
from app.schemas.practice import (
    StartPracticeRequest,
    PracticeSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    PracticeHistoryItem,
    WeakAreaItem,
)

router = APIRouter(prefix="/practice", tags=["Practice & Assessment Engine"])


@router.post("/sessions/start", response_model=PracticeSessionResponse)
async def start_practice_session(
    request: StartPracticeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initializes an adaptive practice or exam session with structured questions
    covering MCQ, multiple-select, true/false, fill-in-blank, scenario, or coding questions.
    """
    try:
        service = PracticeService(db)
        session_data = await service.start_session(
            user_id=current_user.id,
            topic=request.topic,
            session_mode=request.session_mode,
            count=request.count,
            difficulty=request.difficulty,
            document_id=request.document_id,
        )
        return session_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start practice session: {str(e)}",
        )


@router.post("/sessions/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_practice_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates a student's answer, awards partial credit, diagnoses distractors and
    misconceptions, updates evidence-based mastery in StudentMastery, and returns the next question.
    """
    try:
        service = PracticeService(db)
        result = await service.submit_answer(
            user_id=current_user.id,
            session_id=session_id,
            question_id=request.question_id,
            student_response=request.student_response,
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
            detail=f"Failed to evaluate answer: {str(e)}",
        )


@router.get("/history", response_model=List[PracticeHistoryItem])
async def get_practice_history(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the student's historical practice sessions and scores.
    """
    service = PracticeService(db)
    return await service.get_practice_history(user_id=current_user.id, limit=limit)


@router.get("/weak-areas", response_model=List[WeakAreaItem])
async def get_student_weak_areas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregates diagnosed weak areas, misconceptions, and recommended remediation
    actions from StudentMastery evidence.
    """
    service = PracticeService(db)
    return await service.get_weak_areas(user_id=current_user.id)
