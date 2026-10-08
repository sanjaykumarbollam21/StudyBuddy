from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StartPracticeRequest(BaseModel):
    topic: str = Field(..., description="Topic or subject for practice questions")
    session_mode: str = Field("practice", description="practice, timed, or exam")
    count: int = Field(5, ge=1, le=25, description="Number of questions in session")
    difficulty: Optional[str] = Field(None, description="beginner, intermediate, or advanced")
    document_id: Optional[str] = Field(None, description="Optional uploaded document ID for grounded questions")


class QuestionItemResponse(BaseModel):
    id: str
    order_index: int
    question_type: str
    prompt: str
    options: List[str] = []
    difficulty: str = "medium"
    learning_objective: Optional[str] = None
    concept_tag: Optional[str] = None


class PracticeSessionResponse(BaseModel):
    session_id: str
    title: str
    topic: str
    session_mode: str = "practice"
    total_questions: int
    current_question_index: int = 0
    status: str = "in_progress"
    current_question: Optional[QuestionItemResponse] = None


class SubmitAnswerRequest(BaseModel):
    question_id: str
    student_response: str


class EvaluationDetails(BaseModel):
    verdict: str
    is_correct: bool
    score: float
    feedback: str
    explanation: str
    misconception_identified: Optional[str] = None
    remediation_advice: Optional[str] = None
    concept_tag: Optional[str] = None


class SubmitAnswerResponse(BaseModel):
    evaluation: EvaluationDetails
    session_score_percentage: float
    updated_mastery_percentage: float
    is_session_completed: bool
    current_question_index: int
    total_questions: int
    next_question: Optional[QuestionItemResponse] = None


class PracticeHistoryItem(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    session_mode: str
    total_questions: int
    score_percentage: float
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class WeakAreaItem(BaseModel):
    topic: str
    mastery_percentage: float
    times_practiced: int
    primary_misconception: str
    total_misconceptions_logged: int
    remediation_action: str
