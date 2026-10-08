from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class QuestionType(str, Enum):
    MCQ = "mcq"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"
    SCENARIO = "scenario"
    CODING = "coding"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EvaluationVerdict(str, Enum):
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"


@dataclass
class GeneratedQuestion:
    id: str
    question_type: QuestionType
    prompt: str
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    distractor_explanations: Dict[str, str] = field(default_factory=dict)
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_objective: str = ""
    concept_tag: str = ""
    order_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question_type": self.question_type.value,
            "prompt": self.prompt,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "distractor_explanations": self.distractor_explanations,
            "difficulty": self.difficulty.value,
            "learning_objective": self.learning_objective,
            "concept_tag": self.concept_tag,
            "order_index": self.order_index,
        }


@dataclass
class PracticeEvaluation:
    verdict: EvaluationVerdict
    is_correct: bool
    score: float  # 0.0 to 1.0 (supports partial credit)
    feedback: str
    explanation: str
    misconception_identified: Optional[str] = None
    remediation_advice: Optional[str] = None
    concept_tag: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "is_correct": self.is_correct,
            "score": self.score,
            "feedback": self.feedback,
            "explanation": self.explanation,
            "misconception_identified": self.misconception_identified,
            "remediation_advice": self.remediation_advice,
            "concept_tag": self.concept_tag,
        }
