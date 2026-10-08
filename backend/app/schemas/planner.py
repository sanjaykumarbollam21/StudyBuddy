from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class StudyPlanCreateRequest(BaseModel):
    title: Optional[str] = None
    subject: str = "Operating Systems"
    exam_date: Optional[datetime] = None
    days_until_exam: Optional[int] = 12
    daily_study_minutes: int = 120  # 2 hours per day
    focus_weak_areas: bool = True


class StudyPlanItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    day_number: int
    scheduled_date: Optional[datetime] = None
    session_type: str
    topic: str
    allocated_minutes: int
    priority_weight: float
    status: str
    action_type: str
    action_payload: Dict[str, Any] = {}
    completed_at: Optional[datetime] = None
    performance_score: Optional[float] = None
    notes: Optional[str] = None


class StudyPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    subject: str
    exam_date: Optional[datetime] = None
    daily_study_minutes: int
    total_days: int
    total_available_hours: float
    current_day: int
    status: str
    strategy_summary: Dict[str, Any] = {}
    last_replanned_at: Optional[datetime] = None
    items: List[StudyPlanItemResponse] = []
    today_items: List[StudyPlanItemResponse] = []
    progress_percentage: float = 0.0


class ReplanRequest(BaseModel):
    missed_days: Optional[int] = 0
    new_exam_date: Optional[datetime] = None
    new_days_until_exam: Optional[int] = None
    new_daily_study_minutes: Optional[int] = None
    reason: Optional[str] = "Student requested re-plan"


class MicroSessionRequest(BaseModel):
    minutes: int = Field(default=30, ge=10, le=180)
    preferred_type: Optional[str] = None


class MicroSessionResponse(BaseModel):
    allocated_minutes: int
    recommended_topic: str
    session_type: str
    action_type: str
    action_payload: Dict[str, Any]
    pedagogical_reasoning: str


class AgentActionPayload(BaseModel):
    action_type: str  # socratic_lesson, active_recall, practice_quiz, mock_exam, replan_view
    topic: str
    subject: str
    duration_minutes: int = 30
    metadata: Dict[str, Any] = {}


class AgentChatRequest(BaseModel):
    message: str
    plan_id: Optional[str] = None
    context_minutes: Optional[int] = None


class AgentChatResponse(BaseModel):
    message: str
    intent: str
    reasoning: str
    suggested_action: Optional[AgentActionPayload] = None
    today_items: List[StudyPlanItemResponse] = []
    plan_summary: Dict[str, Any] = {}
