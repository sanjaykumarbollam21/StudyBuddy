from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text, Boolean, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class AgentTask(Base):
    """
    Phase 12 & 13: Autonomous Agent Task entity.
    Tracks goals, multi-factor decision reasons, safety permission levels,
    orchestrated steps, execution outcomes, and granular step-level resumption.
    """
    __tablename__ = "agent_tasks"
    __table_args__ = (
        Index("ix_agent_tasks_user_state", "user_id", "current_state"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    priority = Column(String(50), default="high")  # critical, high, medium, low
    permission_level = Column(String(50), default="requires_permission")  # recommend, requires_permission, autonomous
    current_state = Column(String(50), default="proposed")  # proposed, approved, executing, paused, completed, rejected, cancelled
    proposed_actions = Column(JSON, default=list)  # [{"step": 1, "type": "reteach", "topic": "Deadlocks", ...}]
    current_step_index = Column(Integer, default=0)
    step_progress = Column(JSON, default=dict)  # {"1": {"status": "completed", ...}, "2": {"status": "in_progress", ...}}
    is_resumable = Column(Boolean, default=True)
    execution_result = Column(JSON, default=dict)  # {"steps_completed": [...], "mastery_delta": +15.0}
    explanation_breakdown = Column(JSON, default=dict)  # {"mastery_gap": 0.52, "exam_weight": 0.15, ...}
    allocated_minutes = Column(Integer, default=45)
    interrupted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="agent_tasks")
