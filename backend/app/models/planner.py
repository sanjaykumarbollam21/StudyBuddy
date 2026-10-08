from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class StudyPlan(Base):
    """
    Long-term active study plan created and continuously dynamically re-planned by the Study Planner Agent.
    """
    __tablename__ = "study_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False, default="Operating Systems")
    exam_date = Column(DateTime, nullable=True)
    daily_study_minutes = Column(Integer, default=120)  # default 2 hours / day
    total_days = Column(Integer, default=12)
    total_available_hours = Column(Float, default=24.0)
    current_day = Column(Integer, default=1)
    status = Column(String(50), default="active")  # active, completed, paused, archived
    strategy_summary = Column(JSON, default=dict)  # {"phases": [...], "high_yield_topics": [...], "rationale": "..."}
    last_replanned_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    items = relationship("StudyPlanItem", back_populates="plan", cascade="all, delete-orphan", order_by="StudyPlanItem.day_number")


class StudyPlanItem(Base):
    """
    Individual scheduled study session block within a dynamic study plan.
    Links directly to Socratic teaching, active recall, practice quizzes, or mock exams.
    """
    __tablename__ = "study_plan_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False, default=1)
    scheduled_date = Column(DateTime, default=utc_now)
    session_type = Column(String(50), nullable=False, default="learn")  # learn, practice, revision, mock_exam, weak_repair
    topic = Column(String(255), nullable=False)
    allocated_minutes = Column(Integer, default=45)
    priority_weight = Column(Float, default=0.5)  # 0.0 to 1.0 based on weak area, blueprint, prerequisites
    status = Column(String(50), default="pending")  # pending, in_progress, completed, skipped
    action_type = Column(String(50), default="socratic_lesson")  # socratic_lesson, active_recall, practice_quiz, mock_exam
    action_payload = Column(JSON, default=dict)  # {"topic": "Deadlocks", "question_count": 20, "subject": "Operating Systems"}
    completed_at = Column(DateTime, nullable=True)
    performance_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    plan = relationship("StudyPlan", back_populates="items")
