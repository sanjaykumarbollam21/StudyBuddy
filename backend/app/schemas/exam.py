from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ExamConfigRequest(BaseModel):
    title: str = Field(...)
    subject: str = Field(default="Operating Systems")
    total_marks: int = Field(default=100, ge=10, le=500)
    duration_minutes: int = Field(default=60, ge=5, le=360)
    negative_marking_ratio: float = Field(default=0.25, ge=0.0, le=1.0)
    blueprint: Optional[Dict[str, float]] = None
    difficulty_mix: Optional[Dict[str, float]] = None
    exam_date: Optional[datetime] = None


class ExamConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    subject: str
    total_marks: int
    duration_minutes: int
    passing_percentage: float
    negative_marking_ratio: float
    blueprint: Dict[str, float]
    difficulty_mix: Dict[str, float]
    exam_date: Optional[datetime]
    created_at: datetime


class StartMockExamRequest(BaseModel):
    config_id: Optional[str] = None
    subject: str = "Operating Systems"
    total_questions: int = Field(default=10, ge=3, le=50)


class ExamQuestionItem(BaseModel):
    id: str
    topic: str
    question_type: str
    prompt: str
    options: List[str] = []
    marks: float
    negative_marks: float
    order_index: int
    difficulty: str
    concept_tag: Optional[str] = None
    learning_objective: Optional[str] = None


class MockExamSessionResponse(BaseModel):
    id: str
    exam_config_id: Optional[str]
    title: str
    subject: str
    duration_minutes: int
    time_remaining_seconds: int
    status: str
    total_questions: int
    total_marks: float
    questions: List[ExamQuestionItem]
    review_flags: List[str] = []
    answers_record: Dict[str, Any] = {}


class SaveExamProgressRequest(BaseModel):
    answers: Dict[str, Any] = {}
    review_flags: List[str] = []
    time_remaining_seconds: int = 3600


class SubmitExamRequest(BaseModel):
    answers: Optional[Dict[str, Any]] = None
    time_spent_seconds: Optional[int] = None


class TopicPerformanceItem(BaseModel):
    topic: str
    score_percentage: float
    tier: str  # Strong, Good, Weak, Critical
    correct_count: int
    question_count: int
    marks_obtained: float
    total_marks: float


class CognitiveDiagnosis(BaseModel):
    core_issue: str
    deep_explanation: str
    key_remediation_concept: str
    detected_misconceptions_count: int
    unanswered_questions: int


class RemediationAction(BaseModel):
    target_topic: str
    cta_title: str
    prompt: str
    learning_objective: str


class ExamReadinessDetail(BaseModel):
    readiness_percentage: float
    readiness_category: str
    readiness_message: str
    actionable_projection: str
    dimension_scores: Dict[str, float]
    strong_topics: List[str]
    weak_topics: List[str]
    critical_topics: List[str]


class ExamResultResponse(BaseModel):
    id: str
    title: str
    status: str
    score_percentage: float
    marks_obtained: float
    total_marks: float
    negative_marks_deducted: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    topic_analysis: List[TopicPerformanceItem]
    cognitive_diagnosis: CognitiveDiagnosis
    remediation_action: RemediationAction
    readiness: ExamReadinessDetail


class ExamReadinessResponse(BaseModel):
    exam_title: str
    subject: str
    exam_date: Optional[str]
    readiness_percentage: float
    readiness_category: str
    readiness_message: str
    actionable_projection: str
    dimension_scores: Dict[str, float]
    strong_topics: List[str]
    weak_topics: List[str]
    critical_topics: List[str]
