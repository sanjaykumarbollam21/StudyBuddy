from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class AgentActionStep(BaseModel):
    step: int
    type: str  # reteach, practice, revision, mock_exam, update_mastery, replan
    topic: str
    duration_mins: int
    engine: str  # TeacherEngine, PracticeEngine, RevisionEngine, ExamEngine, PlannerEngine
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(BaseModel):
    id: str
    user_id: str
    goal: str
    reason: str
    priority: str  # critical, high, medium, low
    permission_level: str  # recommend, requires_permission, autonomous
    current_state: str  # proposed, approved, executing, paused, completed, rejected, cancelled
    proposed_actions: List[Dict[str, Any]]
    current_step_index: int = 0
    step_progress: Dict[str, Any] = Field(default_factory=dict)
    is_resumable: bool = True
    execution_result: Dict[str, Any] = Field(default_factory=dict)
    explanation_breakdown: Dict[str, Any] = Field(default_factory=dict)
    allocated_minutes: int
    interrupted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdvanceStepRequest(BaseModel):
    task_id: str
    step_index: int
    step_result: Dict[str, Any] = Field(default_factory=dict)
    mark_task_completed: bool = False


class ResumeTaskResponse(BaseModel):
    task: AgentTaskResponse
    resumed_step_index: int
    step_description: str
    status_summary: str


class EvaluateStateRequest(BaseModel):
    available_minutes: int = 60
    subject: str = "Operating Systems"
    exam_name: Optional[str] = "Operating Systems Final"
    days_until_exam: Optional[int] = 5


class ProposeTaskRequest(BaseModel):
    goal: str
    reason: str
    priority: str = "high"
    permission_level: str = "requires_permission"
    proposed_actions: List[Dict[str, Any]]
    allocated_minutes: int = 45
    explanation_breakdown: Dict[str, Any] = Field(default_factory=dict)


class ExecuteTaskRequest(BaseModel):
    task_id: str
    auto_apply_planner: bool = True


class ExecuteTaskResponse(BaseModel):
    success: bool
    task_id: str
    current_state: str
    execution_summary: str
    steps_executed: List[Dict[str, Any]]
    mastery_updated: Dict[str, Any]
    planner_updated: bool


class AgentOrchestratorChatRequest(BaseModel):
    message: str
    available_minutes: Optional[int] = 60
    subject: Optional[str] = "Operating Systems"


class AgentOrchestratorChatResponse(BaseModel):
    reply: str
    intent_detected: str
    suggested_task: Optional[AgentTaskResponse] = None
    orchestrated_engines: List[str]
    explainability: Dict[str, Any] = Field(default_factory=dict)
