from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.exam.service import ExamService
from app.schemas.exam import (
    ExamConfigRequest,
    ExamConfigResponse,
    StartMockExamRequest,
    MockExamSessionResponse,
    ExamQuestionItem,
    SaveExamProgressRequest,
    SubmitExamRequest,
    ExamResultResponse,
    ExamReadinessResponse,
    TopicPerformanceItem,
    CognitiveDiagnosis,
    RemediationAction,
    ExamReadinessDetail,
)

router = APIRouter(prefix="/exams", tags=["Exam Readiness & Mock Tests"])


@router.get("/configs", response_model=List[ExamConfigResponse])
async def get_exam_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns configured exam targets and blueprints for the current user.
    """
    try:
        service = ExamService(db)
        return await service.get_configs(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch exam configurations: {str(e)}",
        )


@router.post("/configs", response_model=ExamConfigResponse)
async def create_or_update_exam_config(
    request: ExamConfigRequest,
    config_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates or updates an exam target with customized blueprint, duration, and negative marking.
    """
    try:
        service = ExamService(db)
        return await service.create_or_update_config(
            user_id=current_user.id,
            title=request.title,
            subject=request.subject,
            total_marks=request.total_marks,
            duration_minutes=request.duration_minutes,
            negative_marking_ratio=request.negative_marking_ratio,
            blueprint=request.blueprint,
            difficulty_mix=request.difficulty_mix,
            exam_date=request.exam_date,
            config_id=config_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save exam configuration: {str(e)}",
        )


@router.post("/mock/start", response_model=MockExamSessionResponse)
async def start_mock_exam(
    request: StartMockExamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates and initializes a timed mock exam session adhering to the subject blueprint.
    """
    try:
        service = ExamService(db)
        session = await service.start_mock_exam(
            user_id=current_user.id,
            config_id=request.config_id,
            subject=request.subject,
            total_questions=request.total_questions,
        )

        formatted_questions = [
            ExamQuestionItem(
                id=q["id"],
                topic=q.get("topic", "General"),
                question_type=q.get("question_type", "mcq"),
                prompt=q.get("prompt", ""),
                options=q.get("options", []),
                marks=float(q.get("marks", 10.0)),
                negative_marks=float(q.get("negative_marks", 2.5)),
                order_index=int(q.get("order_index", 1)),
                difficulty=q.get("difficulty", "intermediate"),
                concept_tag=q.get("concept_tag"),
                learning_objective=q.get("learning_objective"),
            )
            for q in (session.questions_data or [])
        ]

        return MockExamSessionResponse(
            id=session.id,
            exam_config_id=session.exam_config_id,
            title=session.title,
            subject=session.subject,
            duration_minutes=session.duration_minutes,
            time_remaining_seconds=session.time_remaining_seconds,
            status=session.status,
            total_questions=session.total_questions,
            total_marks=session.total_marks,
            questions=formatted_questions,
            review_flags=session.review_flags or [],
            answers_record=session.answers_record or {},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start mock exam: {str(e)}",
        )


@router.get("/mock/{session_id}", response_model=MockExamSessionResponse)
async def get_mock_exam(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a mock exam session state (supporting crash recovery and resume).
    """
    try:
        service = ExamService(db)
        session = await service.get_mock_session(user_id=current_user.id, session_id=session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock exam session not found")

        formatted_questions = [
            ExamQuestionItem(
                id=q["id"],
                topic=q.get("topic", "General"),
                question_type=q.get("question_type", "mcq"),
                prompt=q.get("prompt", ""),
                options=q.get("options", []),
                marks=float(q.get("marks", 10.0)),
                negative_marks=float(q.get("negative_marks", 2.5)),
                order_index=int(q.get("order_index", 1)),
                difficulty=q.get("difficulty", "intermediate"),
                concept_tag=q.get("concept_tag"),
                learning_objective=q.get("learning_objective"),
            )
            for q in (session.questions_data or [])
        ]

        return MockExamSessionResponse(
            id=session.id,
            exam_config_id=session.exam_config_id,
            title=session.title,
            subject=session.subject,
            duration_minutes=session.duration_minutes,
            time_remaining_seconds=session.time_remaining_seconds,
            status=session.status,
            total_questions=session.total_questions,
            total_marks=session.total_marks,
            questions=formatted_questions,
            review_flags=session.review_flags or [],
            answers_record=session.answers_record or {},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mock exam: {str(e)}",
        )


@router.put("/mock/{session_id}/progress", response_model=MockExamSessionResponse)
async def save_mock_exam_progress(
    session_id: str,
    request: SaveExamProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Saves in-progress student answers, review flags, and remaining timer for uninterrupted recovery.
    """
    try:
        service = ExamService(db)
        session = await service.save_mock_progress(
            user_id=current_user.id,
            session_id=session_id,
            answers=request.answers,
            review_flags=request.review_flags,
            time_remaining_seconds=request.time_remaining_seconds,
        )

        formatted_questions = [
            ExamQuestionItem(
                id=q["id"],
                topic=q.get("topic", "General"),
                question_type=q.get("question_type", "mcq"),
                prompt=q.get("prompt", ""),
                options=q.get("options", []),
                marks=float(q.get("marks", 10.0)),
                negative_marks=float(q.get("negative_marks", 2.5)),
                order_index=int(q.get("order_index", 1)),
                difficulty=q.get("difficulty", "intermediate"),
                concept_tag=q.get("concept_tag"),
                learning_objective=q.get("learning_objective"),
            )
            for q in (session.questions_data or [])
        ]

        return MockExamSessionResponse(
            id=session.id,
            exam_config_id=session.exam_config_id,
            title=session.title,
            subject=session.subject,
            duration_minutes=session.duration_minutes,
            time_remaining_seconds=session.time_remaining_seconds,
            status=session.status,
            total_questions=session.total_questions,
            total_marks=session.total_marks,
            questions=formatted_questions,
            review_flags=session.review_flags or [],
            answers_record=session.answers_record or {},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save mock exam progress: {str(e)}",
        )


@router.post("/mock/{session_id}/submit", response_model=ExamResultResponse)
async def submit_mock_exam(
    session_id: str,
    request: SubmitExamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits mock exam, computes negative marking, topic performance breakdown,
    cognitive diagnostic analysis, closed-loop reteach handoff, and updated exam readiness.
    """
    try:
        service = ExamService(db)
        session = await service.submit_mock_exam(
            user_id=current_user.id,
            session_id=session_id,
            answers=request.answers,
            time_spent_seconds=request.time_spent_seconds,
        )

        da = session.detailed_analysis or {}
        topic_analysis = [
            TopicPerformanceItem(**t) for t in da.get("topic_analysis", [])
        ]
        cog_diag = CognitiveDiagnosis(**da.get("cognitive_diagnosis", {
            "core_issue": "Evaluation complete.",
            "deep_explanation": "Review individual topic scores below.",
            "key_remediation_concept": "General",
            "detected_misconceptions_count": 0,
            "unanswered_questions": 0,
        }))
        remed = RemediationAction(**da.get("remediation_action", {
            "target_topic": "Deadlocks",
            "cta_title": "Reteach Deadlocks",
            "prompt": "Teach me deadlock prevention vs avoidance.",
            "learning_objective": "Remediate core deadlock concepts.",
        }))
        readiness_raw = da.get("readiness", {})
        readiness_detail = ExamReadinessDetail(
            readiness_percentage=readiness_raw.get("readiness_percentage", 65.0),
            readiness_category=readiness_raw.get("readiness_category", "Moderate Exam Readiness"),
            readiness_message=readiness_raw.get("readiness_message", "You're approximately 65% ready."),
            actionable_projection=readiness_raw.get("actionable_projection", "Focus on your weakest topics."),
            dimension_scores=readiness_raw.get("dimension_scores", {}),
            strong_topics=readiness_raw.get("strong_topics", []),
            weak_topics=readiness_raw.get("weak_topics", []),
            critical_topics=readiness_raw.get("critical_topics", []),
        )

        return ExamResultResponse(
            id=session.id,
            title=session.title,
            status=session.status,
            score_percentage=session.score_percentage,
            marks_obtained=session.marks_obtained,
            total_marks=session.total_marks,
            negative_marks_deducted=session.negative_marks_deducted,
            correct_count=da.get("correct_count", 0),
            incorrect_count=da.get("incorrect_count", 0),
            unanswered_count=da.get("unanswered_count", 0),
            topic_analysis=topic_analysis,
            cognitive_diagnosis=cog_diag,
            remediation_action=remed,
            readiness=readiness_detail,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit mock exam: {str(e)}",
        )


@router.get("/readiness", response_model=ExamReadinessResponse)
async def get_exam_readiness(
    config_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes holistic exam readiness across coverage, mastery, active recall,
    practice accuracy, mock tests, and time management.
    """
    try:
        service = ExamService(db)
        return await service.get_readiness_analysis(
            user_id=current_user.id,
            config_id=config_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute exam readiness: {str(e)}",
        )
