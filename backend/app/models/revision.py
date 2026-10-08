from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text, JSON, Index
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class RevisionItem(Base):
    __tablename__ = "revision_items"
    __table_args__ = (
        Index("ix_revision_items_user_due", "user_id", "next_review_date"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), nullable=True)
    topic_title = Column(String(255), nullable=False)
    concept_summary = Column(Text, nullable=True)
    retrieval_prompt = Column(Text, nullable=False)
    retrieval_answer = Column(Text, nullable=False)
    last_studied_at = Column(DateTime, default=utc_now)
    repetition_interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)  # SuperMemo SM-2 multiplier (min 1.3)
    repetition_count = Column(Integer, default=0)
    next_review_date = Column(DateTime, default=utc_now, nullable=False)
    mastery_score = Column(Float, default=0.0)
    is_due = Column(Boolean, default=True)
    quality_history = Column(JSON, default=list)  # List of historical ratings [3, 4, 5, 2]
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
