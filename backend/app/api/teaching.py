from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.search.hybrid import KnowledgeSearchService
from app.embeddings import get_embedding_provider
from app.tutor.providers import get_llm_provider
from app.teaching.models import (
    StartTeachingRequest,
    StudentResponseRequest,
    TeacherTurnResponse,
    TeachingSessionModel,
    ActiveSessionSummary,
)
from app.teaching.engine import TeachingEngine
from app.teaching.service import TeachingSessionService

router = APIRouter(prefix="/teaching", tags=["AI Teaching Engine"])

@router.post("/start", response_model=TeacherTurnResponse)
async def start_teaching_session(
    request: StartTeachingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new structured pedagogical teaching session for a topic or document.
    Begins with Socratic goal assessment and prior knowledge check.
    """
    search_service = KnowledgeSearchService(db, get_embedding_provider())
    llm_provider = get_llm_provider()
    engine = TeachingEngine(db_session=db, search_service=search_service, llm_provider=llm_provider)

    try:
        response = await engine.start_session(
            user_id=current_user.id,
            topic=request.topic,
            subject=request.subject or "General",
            document_id=request.document_id,
            student_goal=request.student_goal,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start teaching session: {str(e)}",
        )

@router.post("/{session_id}/interact", response_model=TeacherTurnResponse)
async def interact_with_teacher(
    session_id: str,
    request: StudentResponseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send student response or hint request to the AI Teacher.
    Evaluates comprehension, remediates misconceptions, and advances mastery.
    """
    search_service = KnowledgeSearchService(db, get_embedding_provider())
    llm_provider = get_llm_provider()
    engine = TeachingEngine(db_session=db, search_service=search_service, llm_provider=llm_provider)

    try:
        response = await engine.process_student_turn(
            session_id=session_id,
            student_answer=request.answer,
            action_type=request.action_type or "answer",
        )
        return response
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teaching session '{session_id}' not found.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating student response: {str(e)}",
        )

@router.get("/sessions/active", response_model=List[ActiveSessionSummary])
async def get_active_teaching_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all active (incomplete) teaching sessions for the authenticated student.
    Returns session id, topic/concept title, current step index and total steps,
    mastery score, and last-updated time, scoped strictly to the authenticated user.
    """
    sessions = await TeachingSessionService.get_active_sessions_for_user(db, current_user.id)
    return [
        ActiveSessionSummary(
            session_id=s.session_id,
            topic=s.topic,
            concept_title=s.current_step.title if s.current_step else s.topic,
            current_step_index=s.current_step_index,
            total_steps=s.total_steps if s.total_steps > 0 else 1,
            mastery_score=s.mastery_score,
            updated_at=s.updated_at,
            last_updated=s.updated_at,
        )
        for s in sessions
    ]

@router.get("/{session_id}", response_model=TeachingSessionModel)
async def get_teaching_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the complete state, steps, and dialogue history of a teaching session.
    """
    engine = TeachingEngine(db_session=db)
    session = await engine.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teaching session '{session_id}' not found.",
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Session belongs to another student.",
        )
    return session
