from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RevisionItemResponse(BaseModel):
    id: str
    topic_title: str
    concept_summary: Optional[str] = None
    retrieval_prompt: str
    retrieval_answer: str
    interval_days: int
    repetition_count: int
    ease_factor: float
    mastery_score: float
    days_overdue: float
    quality_history: List[int] = []


class SubmitReviewRequest(BaseModel):
    item_id: str
    quality_rating: int = Field(..., ge=0, le=5, description="Recall quality from 0 (blackout) to 5 (perfect)")
    student_recall: Optional[str] = Field(None, description="Optional text recalled by student")


class SubmitReviewResponse(BaseModel):
    item_id: str
    topic_title: Optional[str] = None
    quality_rating: int
    is_passed: bool
    new_interval_days: int
    new_ease_factor: float
    next_review_date: str
    updated_mastery_percentage: float
    remediation_advice: Optional[str] = None


class ContinueLearningInfo(BaseModel):
    topic: str
    progress_text: str
    subject: str


class WeakAreaInfo(BaseModel):
    concept: str
    mastery_percentage: float
    topic: str


class DailyAgendaResponse(BaseModel):
    continue_learning: ContinueLearningInfo
    due_for_review_count: int
    top_weak_area: WeakAreaInfo
    recommended_action: str
    exam_priority: str
    review_streak_days: int
    retention_rate_percentage: float
