from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateRoadmapRequest(BaseModel):
    subject: str = Field(..., description="Subject or track name (e.g. Operating Systems, DBMS, Machine Learning)")
    goal: Optional[str] = Field(None, description="Student's personal learning goal or target outcome")
    document_id: Optional[str] = Field(None, description="Optional uploaded document ID to extract curriculum from")


class RoadmapTopicItem(BaseModel):
    id: Optional[str] = None
    order_index: int
    custom_title: str
    description: Optional[str] = None
    difficulty: str = "medium"
    estimated_minutes: int = 30
    status: str = "locked"  # locked, unlocked, in_progress, mastered
    mastery_score: float = 0.0
    prerequisites: List[str] = []
    sub_concepts: List[str] = []
    learning_objectives: List[str] = []


class RoadmapResponse(BaseModel):
    id: str
    title: str
    subject: Optional[str] = None
    goal: Optional[str] = None
    source_type: str = "foundational"
    total_steps: int
    completed_steps: int
    progress_percentage: float
    status: str = "in_progress"
    topics: List[RoadmapTopicItem] = []


class NextRecommendationResponse(BaseModel):
    roadmap_id: str
    roadmap_title: str
    topic_title: str
    description: str = ""
    difficulty: str = "medium"
    estimated_minutes: int = 30
    status: str = "in_progress"
    prerequisites: List[str] = []
    learning_objectives: List[str] = []
    why_recommended: str


class WhyLearningResponse(BaseModel):
    topic_title: str
    prerequisites: List[str] = []
    unlocked_next: List[str] = []
    full_explanation: str
    core_value: str
    prerequisite_connection: str
    future_unlocks: str
