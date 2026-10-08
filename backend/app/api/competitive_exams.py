from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.competitive_exam import CompetitiveExamProfile
from app.api.deps import get_current_user, get_optional_current_user
from app.exam.profiles.registry import ExamProfileRegistry
from app.exam.syllabus_service import SyllabusService
from app.exam.pyq_service import PYQService
from app.exam.current_affairs_service import CurrentAffairsService
from app.exam.answer_writing_service import AnswerWritingService
from app.exam.csat_engine import CSATEngine
from app.exam.adaptive_mock_service import AdaptiveMockService
from app.exam.readiness_dashboard_service import ReadinessDashboardService

router = APIRouter(prefix="/competitive-exams", tags=["Competitive Examination Intelligence"])


# --- Schemas ---

class ProfileUpdateRequest(BaseModel):
    exam_id: str = "upsc_cse"
    target_year: int = 2027
    target_date: Optional[str] = None
    current_stage: str = "prelims"
    optional_subject: Optional[str] = None
    daily_target_hours: float = 6.0
    language: str = "English"
    daf_details: Optional[Dict[str, Any]] = None


class PYQAttemptRequest(BaseModel):
    question_id: str
    selected_option: str
    time_taken_seconds: int = 45


class AnswerWritingEvaluationRequest(BaseModel):
    question_text: str
    student_answer_text: str
    topic_code: Optional[str] = "GS2-POLITY-01"
    paper_id: str = "gs2"
    word_limit: int = 250
    allocated_marks: float = 15.0


class AdaptiveMockRequest(BaseModel):
    exam_id: str = "upsc_cse"
    paper_id: str = "prelims_gs1"
    question_count: int = 20


# --- Endpoints ---

@router.get("/profiles")
async def list_supported_exam_profiles():
    """Lists all available competitive exam definitions (UPSC, SSC, Banking, GATE, JEE, NEET, etc.)."""
    return ExamProfileRegistry.list_all_profiles()


@router.get("/profile/current")
async def get_current_exam_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetches user's current active competitive exam target profile."""
    res = await db.execute(
        select(CompetitiveExamProfile).where(
            CompetitiveExamProfile.user_id == current_user.id,
            CompetitiveExamProfile.is_primary.is_(True),
        )
    )
    profile = res.scalar_one_or_none()
    if not profile:
        profile = CompetitiveExamProfile(
            user_id=current_user.id,
            exam_id="upsc_cse",
            exam_name="UPSC Civil Services Examination",
            target_year=2027,
            current_stage="prelims",
            daily_target_hours=6.0,
            is_primary=True,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return {
        "id": profile.id,
        "exam_id": profile.exam_id,
        "exam_name": profile.exam_name,
        "target_year": profile.target_year,
        "target_date": profile.target_date.isoformat() if profile.target_date else None,
        "current_stage": profile.current_stage,
        "optional_subject": profile.optional_subject,
        "daily_target_hours": profile.daily_target_hours,
        "language": profile.language,
        "daf_details": profile.daf_details or {},
    }


@router.post("/profile")
async def update_exam_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sets or updates user's target competitive examination configuration."""
    exam_def = ExamProfileRegistry.get(req.exam_id)
    exam_name = exam_def.name if exam_def else req.exam_id.upper().replace("_", " ")

    res = await db.execute(
        select(CompetitiveExamProfile).where(
            CompetitiveExamProfile.user_id == current_user.id,
            CompetitiveExamProfile.is_primary.is_(True),
        )
    )
    profile = res.scalar_one_or_none()

    target_dt = None
    if req.target_date:
        try:
            target_dt = datetime.fromisoformat(req.target_date)
        except Exception:
            target_dt = None

    if profile:
        profile.exam_id = req.exam_id
        profile.exam_name = exam_name
        profile.target_year = req.target_year
        profile.target_date = target_dt
        profile.current_stage = req.current_stage
        profile.optional_subject = req.optional_subject
        profile.daily_target_hours = req.daily_target_hours
        profile.language = req.language
        if req.daf_details is not None:
            profile.daf_details = req.daf_details
    else:
        profile = CompetitiveExamProfile(
            user_id=current_user.id,
            exam_id=req.exam_id,
            exam_name=exam_name,
            target_year=req.target_year,
            target_date=target_dt,
            current_stage=req.current_stage,
            optional_subject=req.optional_subject,
            daily_target_hours=req.daily_target_hours,
            language=req.language,
            daf_details=req.daf_details or {},
            is_primary=True,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    return {
        "status": "success",
        "profile": {
            "id": profile.id,
            "exam_id": profile.exam_id,
            "exam_name": profile.exam_name,
            "target_year": profile.target_year,
            "current_stage": profile.current_stage,
            "optional_subject": profile.optional_subject,
            "daily_target_hours": profile.daily_target_hours,
        },
    }


@router.get("/syllabus/{exam_id}")
async def get_syllabus_graph(
    exam_id: str,
    stage: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the full hierarchical syllabus DAG with mastery overlay and topic heatmaps."""
    service = SyllabusService(db)
    return await service.get_syllabus_graph(
        user_id=current_user.id,
        exam_id=exam_id,
        stage=stage,
    )


@router.get("/pyqs")
async def get_previous_year_questions(
    exam_id: str = Query("upsc_cse"),
    subject: Optional[str] = Query(None),
    topic_code: Optional[str] = Query(None),
    year_start: Optional[int] = Query(None),
    year_end: Optional[int] = Query(None),
    stage: Optional[str] = Query("prelims"),
    page: int = Query(1, ge=1),
    page_size: Optional[int] = Query(None, le=100),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Filters previous year questions with pagination support."""
    effective_limit = page_size or limit
    service = PYQService(db)
    items = await service.get_filtered_pyqs(
        exam_id=exam_id,
        subject=subject,
        topic_code=topic_code,
        year_start=year_start,
        year_end=year_end,
        stage=stage,
        limit=effective_limit * page,
    )
    start_idx = (page - 1) * effective_limit
    return items[start_idx:start_idx + effective_limit]


@router.post("/pyq/attempt")
async def evaluate_pyq_attempt(
    req: PYQAttemptRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submits a student's answer to a PYQ and returns scoring, explanation, and cognitive error taxonomy."""
    user_id = current_user.id if current_user else "guest-student"
    service = PYQService(db)
    return await service.evaluate_attempt(
        user_id=user_id,
        question_id=req.question_id,
        selected_option=req.selected_option,
        time_taken_seconds=req.time_taken_seconds,
    )


@router.get("/current-affairs")
async def get_current_affairs_feed(
    exam_id: str = Query("upsc_cse"),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: Optional[int] = Query(None, le=50),
    limit: int = Query(15, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Returns daily high-yield current affairs explicitly linked to static syllabus concepts with pagination."""
    effective_limit = page_size or limit
    service = CurrentAffairsService(db)
    items = await service.get_feed(exam_id=exam_id, category=category, limit=effective_limit * page)
    start_idx = (page - 1) * effective_limit
    return items[start_idx:start_idx + effective_limit]


@router.post("/answer-writing/evaluate")
async def evaluate_mains_answer(
    req: AnswerWritingEvaluationRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates a descriptive/Mains answer across 8 dimensions with actionable rubric scoring and outline feedback."""
    service = AnswerWritingService(db)
    return service.evaluate_answer(
        question_text=req.question_text,
        student_answer=req.student_answer_text,
        total_marks=req.allocated_marks,
        word_limit=req.word_limit,
        paper_name=req.paper_id,
    )


@router.get("/csat/session")
async def get_csat_practice_session(
    difficulty: str = Query("medium"),
    question_count: int = Query(10, le=30),
    topic_filter: Optional[str] = Query(None),
):
    """Returns a timed CSAT practice drill session with reading comprehension and logical aptitude questions."""
    return CSATEngine.generate_practice_session(
        difficulty=difficulty,
        count=question_count,
        topic=topic_filter,
    )


@router.post("/mock/adaptive")
async def create_adaptive_mock(
    req: AdaptiveMockRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Synthesizes an adaptive mock exam blueprint targeting student weakness clusters."""
    service = AdaptiveMockService(db)
    return await service.generate_adaptive_blueprint(
        user_id=current_user.id,
        exam_id=req.exam_id,
        paper_id=req.paper_id,
        question_count=req.question_count,
    )


@router.get("/readiness/{exam_id}")
async def get_readiness_report(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Computes comprehensive multi-dimensional readiness index and topic heatmaps."""
    service = ReadinessDashboardService(db)
    return await service.get_readiness_report(
        user_id=current_user.id,
        exam_id=exam_id,
    )
