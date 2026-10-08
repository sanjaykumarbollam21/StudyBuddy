from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Index, Boolean
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Topic(Base):
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = Column(String(36), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    difficulty = Column(String(50), default="medium")
    estimated_mins = Column(Integer, default=30)
    created_at = Column(DateTime, default=utc_now)


class TopicRelation(Base):
    __tablename__ = "topic_relations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    child_topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(50), default="prerequisite")  # prerequisite, depends_on, related_to, extends


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(String(36), nullable=True)
    title = Column(String(255), nullable=False)
    goal = Column(String(1000), nullable=True)
    source_type = Column(String(50), default="user_materials")  # user_materials, web_research, foundational, hybrid
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    status = Column(String(50), default="in_progress")  # not_started, in_progress, completed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class LearningPathTopic(Base):
    __tablename__ = "learning_path_topics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learning_path_id = Column(String(36), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    custom_title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    difficulty = Column(String(50), default="medium")
    estimated_minutes = Column(Integer, default=30)
    status = Column(String(50), default="locked")  # locked, unlocked, in_progress, mastered
    prerequisites = Column(JSON, default=list)  # list of prerequisite titles or ids
    learning_objectives = Column(JSON, default=list)  # list of key objectives
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class StudentMastery(Base):
    __tablename__ = "student_mastery"
    __table_args__ = (
        Index("ix_student_mastery_user_topic", "user_id", "topic_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), nullable=False, index=True)
    mastery_percentage = Column(Float, default=0.0)
    times_practiced = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)
    last_evaluated_at = Column(DateTime, default=utc_now)
    weak_areas = Column(JSON, default=list)


class TeachingSessionDB(Base):
    """
    Persistent model for active pedagogical teaching sessions.
    Uses pure, portable SQLAlchemy types (JSON, String, DateTime, Float, Boolean, Integer)
    guaranteeing seamless compatibility across SQLite and PostgreSQL.
    """
    __tablename__ = "teaching_sessions"
    __table_args__ = (
        Index("ix_teaching_sessions_user_created", "user_id", "created_at"),
        Index("ix_teaching_sessions_user_completed", "user_id", "is_completed"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), default="General", nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_name = Column(String(255), nullable=True)
    current_state = Column(String(50), default="assess_prior_knowledge", nullable=False)
    current_step_index = Column(Integer, default=0, nullable=False)
    steps = Column(JSON, default=list, nullable=False)
    dialogue = Column(JSON, default=list, nullable=False)
    struggle_count = Column(Integer, default=0, nullable=False)
    mastery_score = Column(Float, default=0.0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False, index=True)


