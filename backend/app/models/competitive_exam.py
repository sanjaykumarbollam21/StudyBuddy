from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text, Boolean, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CompetitiveExamProfile(Base):
    """
    Pluggable student exam target profile (UPSC, SSC, Banking, GATE, JEE, NEET, etc.)
    Tracks target year, exam stage, optional subject, and user-configured goals.
    """
    __tablename__ = "competitive_exam_profiles"
    __table_args__ = (
        Index("ix_comp_exam_profiles_user", "user_id"),
        Index("ix_comp_exam_profiles_exam_user", "exam_id", "user_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(String(50), nullable=False, default="upsc_cse")  # upsc_cse, ssc_cgl, ibps_po, gate, jee, neet, state_psc, custom
    exam_name = Column(String(100), nullable=False, default="UPSC Civil Services Examination")
    target_year = Column(Integer, default=2027)
    target_date = Column(DateTime, nullable=True)
    current_stage = Column(String(50), default="prelims")  # prelims, mains, interview, comprehensive
    optional_subject = Column(String(100), nullable=True)  # e.g. "Public Administration", "History", "Physics"
    language = Column(String(50), default="English")
    daily_target_hours = Column(Float, default=6.0)
    daf_details = Column(JSON, default=dict)  # Detailed Application Form (DAF) for interview prep
    settings = Column(JSON, default=dict)
    version = Column(String(20), default="2027.1")
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)
    source = Column(String(255), default="Official Examination Commission Notification")
    source_url = Column(String(500), nullable=True)
    is_primary = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref="competitive_exam_profiles")


class SyllabusNode(Base):
    """
    Hierarchical syllabus graph entity (Subject -> Module -> Topic -> Subtopic).
    Maps exam relevance, PYQ frequency, prerequisites, and student mastery.
    """
    __tablename__ = "syllabus_nodes"
    __table_args__ = (
        Index("ix_syllabus_nodes_exam", "exam_id"),
        Index("ix_syllabus_nodes_parent", "parent_id"),
        Index("ix_syllabus_nodes_stage", "exam_id", "stage"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_id = Column(String(50), nullable=False)
    parent_id = Column(String(36), ForeignKey("syllabus_nodes.id", ondelete="CASCADE"), nullable=True)
    node_code = Column(String(50), nullable=False)  # e.g. "POL-CONST-FR-01"
    title = Column(String(255), nullable=False)  # e.g. "Fundamental Rights"
    description = Column(Text, nullable=True)
    stage = Column(String(50), default="both")  # prelims, mains, both, interview
    paper_name = Column(String(100), default="GS Paper I")  # e.g. "General Studies Paper I", "CSAT Paper II", "GS Paper II"
    exam_weight = Column(Float, default=1.0)  # Relative weight / importance multiplier
    importance = Column(String(20), default="high")  # high, medium, low
    pyq_frequency = Column(Integer, default=0)  # Number of historical questions asked
    prerequisites = Column(JSON, default=list)  # List of prerequisite node IDs
    learning_objectives = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    parent = relationship("SyllabusNode", remote_side=[id], back_populates="children")
    children = relationship("SyllabusNode", back_populates="parent", cascade="all, delete-orphan")


class PreviousYearQuestion(Base):
    """
    Authentic Competitive Exam Previous Year Question (PYQ).
    Supports categorization by year, paper, subject, difficulty, and question type.
    """
    __tablename__ = "previous_year_questions"
    __table_args__ = (
        Index("ix_pyq_exam_year", "exam_id", "year"),
        Index("ix_pyq_syllabus", "syllabus_node_id"),
        Index("ix_pyq_stage_paper", "exam_id", "stage", "paper_name"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_id = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    stage = Column(String(50), default="prelims")  # prelims, mains
    paper_name = Column(String(100), default="General Studies Paper I")
    syllabus_node_id = Column(String(36), ForeignKey("syllabus_nodes.id", ondelete="SET NULL"), nullable=True)
    topic_title = Column(String(255), nullable=False)
    subtopic_title = Column(String(255), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="single_correct")  # single_correct, multiple_correct, assertion_reason, statement_based, match_following, chronology, descriptive
    options = Column(JSON, default=list)  # [{"label": "A", "text": "..."}, ...]
    correct_answer = Column(Text, nullable=False)  # "A" or model answer points
    explanation = Column(Text, nullable=False)
    marks = Column(Float, default=2.0)
    negative_marks = Column(Float, default=0.66)  # e.g. -0.66 for UPSC GS
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    exam_trend_note = Column(Text, nullable=True)  # Pedagogical observation on historical recurrence
    source_citation = Column(String(255), default="Official Exam Commission Archive")
    provenance = Column(String(50), default="OFFICIAL_PYQ")  # OFFICIAL_PYQ, AI_SYNTHESIZED_PRACTICE, USER_CREATED
    question_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    syllabus_node = relationship("SyllabusNode", backref="pyqs")


class PYQAttempt(Base):
    """
    Student attempt telemetry on a Previous Year Question.
    Performs deep cognitive diagnostics, categorizing mistake root causes.
    """
    __tablename__ = "pyq_attempts"
    __table_args__ = (
        Index("ix_pyq_attempts_user_pyq", "user_id", "pyq_id"),
        Index("ix_pyq_attempts_user_created", "user_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pyq_id = Column(String(36), ForeignKey("previous_year_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option = Column(String(100), nullable=True)
    is_correct = Column(Boolean, nullable=False)
    marks_awarded = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=60)
    # Granular error classification to diagnose student weaknesses
    error_type = Column(String(50), nullable=True)  # knowledge_gap, reading_error, careless_error, guessing_error, time_pressure, misconception, none
    confidence_level = Column(String(20), default="medium")  # high, medium, low
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", backref="pyq_attempts")
    pyq = relationship("PreviousYearQuestion", backref="attempts")


class CurrentAffairItem(Base):
    """
    Daily high-yield current affair item linked to static syllabus concepts.
    Captures factual summary, background, constitutional articles, and prelims/mains angles.
    """
    __tablename__ = "current_affairs_items"
    __table_args__ = (
        Index("ix_current_affairs_date", "date"),
        Index("ix_current_affairs_category", "category"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime, default=utc_now, nullable=False)
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=False)
    background = Column(Text, nullable=True)
    category = Column(String(50), default="polity")  # polity, economy, environment, science_tech, international, national, security, social_issues, governance
    source = Column(String(150), default="The Hindu / PIB / Indian Express")
    source_url = Column(String(500), nullable=True)
    syllabus_node_ids = Column(JSON, default=list)  # Linked syllabus nodes
    static_concepts = Column(JSON, default=list)  # e.g. ["Article 21", "Right to Privacy", "Puttaswamy Judgment"]
    prelims_pointers = Column(JSON, default=list)  # Direct facts/dates for MCQs
    mains_pointers = Column(JSON, default=list)  # Multidimensional arguments, pros/cons, committee recommendations
    importance = Column(String(20), default="high")  # high, medium, low
    is_cached = Column(Boolean, default=True)  # Cached locally for offline access
    published_at = Column(DateTime, default=utc_now)
    retrieved_at = Column(DateTime, default=utc_now)
    content_hash = Column(String(64), index=True, nullable=True)  # SHA-256 for deduplication
    created_at = Column(DateTime, default=utc_now)


class MainsAnswerSubmission(Base):
    """
    Mains descriptive answer writing submission and multi-rubric evaluation.
    Tracks progressive drafts, dimensional coverage, structural weaknesses, and outlines.
    """
    __tablename__ = "mains_answer_submissions"
    __table_args__ = (
        Index("ix_mains_submissions_user", "user_id"),
        Index("ix_mains_submissions_user_date", "user_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), nullable=True)
    question_text = Column(Text, nullable=False)
    paper_name = Column(String(100), default="GS Paper II")
    syllabus_node_id = Column(String(36), ForeignKey("syllabus_nodes.id", ondelete="SET NULL"), nullable=True)
    student_answer = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=480)  # Standard 7-8 minutes for 10-marker
    total_marks = Column(Float, default=10.0)  # 10 or 15 marks
    marks_obtained = Column(Float, default=0.0)
    score_percentage = Column(Float, default=0.0)
    # Multi-dimensional rubric scores (0-100% per criterion)
    rubric_breakdown = Column(JSON, default=dict)  # content, structure, relevance, analysis, examples, balance, conclusion, presentation
    strengths = Column(JSON, default=list)
    missing_dimensions = Column(JSON, default=list)  # Economic, social, ethical, constitutional, international dimensions missed
    improvement_guidelines = Column(Text, nullable=True)
    model_outline = Column(Text, nullable=True)  # Exemplary answer architecture
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", backref="mains_submissions")
