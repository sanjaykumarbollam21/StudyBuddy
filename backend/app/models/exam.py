from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text, Boolean
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ExamConfig(Base):
    """
    Configuration and blueprint for a target exam.
    Defines topic weighting, duration, marks, difficulty mix, and negative marking rules.
    """
    __tablename__ = "exam_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)  # e.g. "Operating Systems Midterm Exam"
    subject = Column(String(100), nullable=False)  # e.g. "Operating Systems"
    exam_date = Column(DateTime, nullable=True)
    total_marks = Column(Integer, default=100)
    duration_minutes = Column(Integer, default=60)
    passing_percentage = Column(Float, default=40.0)
    negative_marking_ratio = Column(Float, default=0.25)  # e.g. 0.25 marks deducted per 1 mark wrong
    # Blueprint defines topic distribution weights e.g. {"Processes": 0.15, "CPU Scheduling": 0.15, ...}
    blueprint = Column(JSON, default=dict)
    # Difficulty mix e.g. {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.2}
    difficulty_mix = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class MockExamSession(Base):
    """
    Real simulated exam attempt.
    Tracks live timing, answers, flagged items, negative marking, and post-exam intelligence.
    """
    __tablename__ = "mock_exam_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_config_id = Column(String(36), ForeignKey("exam_configs.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, default=60)
    time_remaining_seconds = Column(Integer, default=3600)
    status = Column(String(50), default="in_progress")  # in_progress, submitted, timed_out
    total_questions = Column(Integer, default=10)
    total_marks = Column(Float, default=100.0)
    marks_obtained = Column(Float, default=0.0)
    score_percentage = Column(Float, default=0.0)
    negative_marks_deducted = Column(Float, default=0.0)
    questions_data = Column(JSON, default=list)  # Serialized generated exam questions
    review_flags = Column(JSON, default=list)  # List of flagged question IDs for review
    answers_record = Column(JSON, default=dict)  # question_id -> {"response": str, "time_spent_seconds": int}
    detailed_analysis = Column(JSON, default=dict)  # Topic breakdown, readiness score, cognitive diagnostic
    started_at = Column(DateTime, default=utc_now)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
