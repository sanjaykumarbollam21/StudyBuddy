from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExamStageConfig:
    stage_id: str
    title: str
    description: str
    paper_names: List[str]
    has_negative_marking: bool = True
    negative_marking_ratio: float = 0.33
    is_descriptive: bool = False


@dataclass
class ExamProfileDefinition:
    """
    Standardized, pluggable specification for any structured competitive or academic examination.
    """
    id: str
    name: str
    category: str
    country: str = "India"
    conducting_body: str = ""
    stages: List[ExamStageConfig] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    syllabus_tree: List[Dict[str, Any]] = field(default_factory=list)
    question_types: List[str] = field(default_factory=list)
    duration_minutes: int = 120
    default_daily_hours: float = 6.0
    has_csat: bool = False
    has_answer_writing: bool = False
    has_negative_marking: bool = True
    negative_marking_ratio: float = 0.33
    marking_scheme: Dict[str, Any] = field(default_factory=dict)
    language_options: List[str] = field(default_factory=lambda: ["English", "Hindi"])

    @property
    def code(self) -> str:
        return self.id

    @property
    def default_negative_marking_ratio(self) -> float:
        return self.negative_marking_ratio

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "country": self.country,
            "conducting_body": self.conducting_body,
            "stages": [
                {
                    "stage_id": s.stage_id,
                    "title": s.title,
                    "description": s.description,
                    "paper_names": s.paper_names,
                    "has_negative_marking": s.has_negative_marking,
                    "negative_marking_ratio": s.negative_marking_ratio,
                    "is_descriptive": s.is_descriptive,
                }
                for s in self.stages
            ],
            "subjects": self.subjects,
            "syllabus_tree": self.syllabus_tree,
            "question_types": self.question_types,
            "duration_minutes": self.duration_minutes,
            "default_daily_hours": self.default_daily_hours,
            "has_csat": self.has_csat,
            "has_answer_writing": self.has_answer_writing,
            "has_negative_marking": self.has_negative_marking,
            "negative_marking_ratio": self.negative_marking_ratio,
            "marking_scheme": self.marking_scheme,
            "language_options": self.language_options,
        }
