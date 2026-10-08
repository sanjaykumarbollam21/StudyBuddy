import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.teaching.state import TeachingState, ConceptStep, StudentDialogueTurn, EvaluationVerdict

class TeachingSessionModel(BaseModel):
    """Full pedagogical teaching session representation."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: str
    subject: str = "General"
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    current_state: TeachingState = TeachingState.ASSESS_PRIOR_KNOWLEDGE
    current_step_index: int = 0
    steps: List[ConceptStep] = Field(default_factory=list)
    dialogue: List[StudentDialogueTurn] = Field(default_factory=list)
    struggle_count: int = 0
    mastery_score: float = 0.0
    is_completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_step(self) -> Optional[ConceptStep]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def total_steps(self) -> int:
        return len(self.steps)

class StartTeachingRequest(BaseModel):
    topic: str
    subject: Optional[str] = None
    document_id: Optional[str] = None
    student_goal: Optional[str] = None

class StudentResponseRequest(BaseModel):
    answer: str
    action_type: Optional[str] = "answer" # "answer", "request_hint", "request_simpler", "skip"

class TeacherTurnResponse(BaseModel):
    session_id: str
    state: TeachingState
    teacher_message: str
    concept_title: Optional[str] = None
    explanation: Optional[str] = None
    analogy: Optional[str] = None
    check_question: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None
    mastery_percentage: float = 0.0
    current_step_number: int = 1
    total_steps: int = 1
    is_lesson_completed: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
    source_citation: Optional[Dict[str, Any]] = None
