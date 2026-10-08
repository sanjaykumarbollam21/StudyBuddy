from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text, Boolean
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(String(36), nullable=True)
    topic_title = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    total_questions = Column(Integer, default=5)
    score_percentage = Column(Float, default=0.0)
    status = Column(String(50), default="in_progress")  # in_progress, completed, abandoned
    session_mode = Column(String(50), default="practice")  # practice, timed, exam
    current_question_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_session_id = Column(String(36), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=True)
    topic_id = Column(String(36), nullable=True)
    topic_title = Column(String(255), nullable=True)
    question_type = Column(String(50), nullable=False)  # mcq, multiple_select, true_false, short_answer, fill_blank, scenario, coding
    prompt = Column(Text, nullable=False)
    options = Column(JSON, default=list)  # list of strings or {"id": "A", "text": "..."}
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    distractor_explanations = Column(JSON, default=dict)  # {"Option B": "Misconception reason"}
    difficulty = Column(String(50), default="medium")  # beginner, intermediate, advanced
    learning_objective = Column(Text, nullable=True)
    concept_tag = Column(String(100), nullable=True)  # e.g. "circular_wait", "mutex", "b_tree"
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_session_id = Column(String(36), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    student_response = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    score_awarded = Column(Float, default=0.0)  # 0.0 to 1.0 (supports partial credit)
    evaluation_feedback = Column(JSON, default=dict)  # {"verdict": "correct", "misconception": "...", "remediation": "..."}
    created_at = Column(DateTime, default=utc_now)
