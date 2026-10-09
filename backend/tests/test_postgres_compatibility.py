import pytest
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from sqlalchemy import create_mock_engine
from app.core.database import Base
import app.models # Ensures all models are registered in Base.metadata
from app.models.learning import TeachingSessionDB


def test_teaching_sessions_table_postgresql_compilation():
    """
    Verify that the TeachingSessionDB model compiles to 100% valid PostgreSQL DDL
    with proper column types (JSON, VARCHAR, TIMESTAMP, BOOLEAN, FLOAT, INTEGER)
    and foreign key constraints.
    """
    table = TeachingSessionDB.__table__
    ddl_str = str(CreateTable(table).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE teaching_sessions" in ddl_str
    assert "steps JSON NOT NULL" in ddl_str
    assert "dialogue JSON NOT NULL" in ddl_str
    assert "is_completed BOOLEAN NOT NULL" in ddl_str
    assert "created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL" in ddl_str
    assert "mastery_score FLOAT NOT NULL" in ddl_str
    assert "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE" in ddl_str

    # Verify all 6 indexes compile cleanly to PostgreSQL syntax
    assert len(table.indexes) >= 6
    for idx in table.indexes:
        idx_ddl = str(CreateIndex(idx).compile(dialect=postgresql.dialect()))
        assert "CREATE INDEX" in idx_ddl
        assert "teaching_sessions" in idx_ddl


def test_all_29_tables_compile_cleanly_to_postgresql_dialect():
    """
    Verify that every table in the application metadata compiles cleanly
    against the PostgreSQL dialect without any unsupported types or dialect errors.
    """
    assert len(Base.metadata.tables) >= 29, f"Expected at least 29 tables, got {len(Base.metadata.tables)}"

    compiled_tables = []
    for name, table in Base.metadata.tables.items():
        table_ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert f"CREATE TABLE {name}" in table_ddl
        for idx in table.indexes:
            idx_ddl = str(CreateIndex(idx).compile(dialect=postgresql.dialect()))
            assert "INDEX" in idx_ddl
        compiled_tables.append(name)

    # Core required tables for the AI Learning Platform
    required_tables = [
        "users",
        "profiles",
        "documents",
        "document_chunks",
        "topics",
        "learning_paths",
        "student_mastery",
        "teaching_sessions",
        "quiz_sessions",
        "revision_items",
        "exam_configs",
        "mock_exam_sessions",
        "study_plans",
        "agent_tasks",
    ]
    for req in required_tables:
        assert req in compiled_tables, f"Missing required table '{req}' in PostgreSQL metadata"


def test_postgresql_mock_engine_create_all():
    """
    Simulates Base.metadata.create_all against a PostgreSQL engine
    verifying all tables, constraints, foreign keys, and sequences
    generate valid DDL statements in sequence.
    """
    executed_statements = []

    def ddl_collector(sql, *multiparams, **params):
        executed_statements.append(str(sql.compile(dialect=engine.dialect)))

    engine = create_mock_engine("postgresql+asyncpg://", ddl_collector)
    Base.metadata.create_all(engine)

    assert len(executed_statements) >= 60, f"Expected at least 60 DDL statements, got {len(executed_statements)}"
    
    # Verify teaching_sessions DDL is included in the execution plan
    found_teaching_sessions = any("teaching_sessions" in stmt for stmt in executed_statements)
    assert found_teaching_sessions, "teaching_sessions was not created in the PostgreSQL create_all plan"


@pytest.mark.asyncio
async def test_teaching_session_postgresql_crud_behavior(db_session):
    """
    Validates end-to-end CRUD operations on TeachingSessionDB
    with JSON serialization/deserialization.
    """
    from datetime import datetime, timezone
    from app.models.user import User
    from app.teaching.service import TeachingSessionService
    from app.teaching.models import TeachingSessionModel
    from app.teaching.state import TeachingState, ConceptStep, StudentDialogueTurn

    user = User(
        id="pg-test-student-1",
        email="pg_student@example.com",
        hashed_password="hashed_pw",
        full_name="Postgres Student",
    )
    db_session.add(user)
    await db_session.commit()

    model = TeachingSessionModel(
        session_id="pg-session-123",
        user_id="pg-test-student-1",
        topic="PostgreSQL Concurrency",
        subject="Database Systems",
        current_state=TeachingState.CHECK_UNDERSTANDING,
        current_step_index=0,
        steps=[
            ConceptStep(
                step_index=0,
                title="MVCC",
                explanation="Multi-Version Concurrency Control maintains snapshots.",
                analogy="A library with instant photo-copies.",
                check_question="Why do readers not block writers?",
                expected_core_concept="Readers see older snapshot tuple versions.",
            )
        ],
        dialogue=[
            StudentDialogueTurn(
                turn_index=0,
                speaker="teacher",
                state=TeachingState.ASSESS_PRIOR_KNOWLEDGE,
                content="What do you know about MVCC?",
            )
        ],
        mastery_score=30.0,
    )

    # 1. Create in DB
    created = await TeachingSessionService.create_session(db_session, model)
    assert created.session_id == "pg-session-123"
    assert created.steps[0].title == "MVCC"

    # 2. Retrieve from DB
    loaded = await TeachingSessionService.get_session(db_session, "pg-session-123")
    assert loaded is not None
    assert loaded.mastery_score == 30.0
    assert len(loaded.dialogue) == 1

    # 3. Update & persist
    loaded.dialogue.append(
        StudentDialogueTurn(
            turn_index=1,
            speaker="student",
            state=TeachingState.CHECK_UNDERSTANDING,
            content="Readers read existing snapshots while writers create new tuples.",
        )
    )
    loaded.mastery_score = 65.0
    await TeachingSessionService.save_session(db_session, loaded)

    reloaded = await TeachingSessionService.get_session(db_session, "pg-session-123")
    assert reloaded is not None
    assert reloaded.mastery_score == 65.0
    assert len(reloaded.dialogue) == 2
