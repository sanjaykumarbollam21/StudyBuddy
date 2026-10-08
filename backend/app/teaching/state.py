from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TeachingState(str, Enum):
    """Pedagogical state machine states for the AI Teacher."""
    DISCOVER_GOAL = "discover_goal"
    ASSESS_PRIOR_KNOWLEDGE = "assess_prior_knowledge"
    TEACH_CONCEPT = "teach_concept"
    CHECK_UNDERSTANDING = "check_understanding"
    EVALUATING = "evaluating"
    RETEACHING = "reteaching"
    ADVANCING = "advancing"
    COMPLETED = "completed"

class EvaluationVerdict(str, Enum):
    """Categorized diagnostic verdict of student comprehension."""
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    MISCONCEPTION = "misconception"
    STRUGGLING = "struggling"
    HINT_REQUESTED = "hint_requested"

class ConceptStep(BaseModel):
    """A discrete, bite-sized pedagogical step within a lesson."""
    step_index: int
    title: str
    explanation: str
    analogy: str
    check_question: str
    expected_core_concept: str
    key_terms: List[str] = Field(default_factory=list)
    common_misconceptions: Dict[str, str] = Field(default_factory=dict)
    simpler_analogy: str = ""
    socratic_hint: str = ""
    source_citation: Optional[Dict[str, Any]] = None

class StudentDialogueTurn(BaseModel):
    """A single turn in the teaching dialogue."""
    turn_index: int
    speaker: str # "teacher" or "student"
    state: TeachingState
    content: str
    concept_title: Optional[str] = None
    question: Optional[str] = None
    evaluation_verdict: Optional[EvaluationVerdict] = None
    feedback: Optional[str] = None
    mastery_delta: float = 0.0
