from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_

from app.models.learning import TeachingSessionDB
from app.teaching.models import TeachingSessionModel
from app.teaching.state import TeachingState, ConceptStep, StudentDialogueTurn


class TeachingSessionService:
    """
    Database persistence, async CRUD, rehydration, and maintenance
    for pedagogical teaching sessions.
    100% portable across SQLite and PostgreSQL.
    """

    @staticmethod
    def _to_pydantic(db_obj: TeachingSessionDB) -> TeachingSessionModel:
        """Converts SQLAlchemy model to Pydantic TeachingSessionModel."""
        try:
            state = TeachingState(db_obj.current_state)
        except Exception:
            state = TeachingState.ASSESS_PRIOR_KNOWLEDGE

        raw_steps = db_obj.steps or []
        steps = [ConceptStep(**s) if isinstance(s, dict) else s for s in raw_steps]

        raw_dialogue = db_obj.dialogue or []
        dialogue = [StudentDialogueTurn(**d) if isinstance(d, dict) else d for d in raw_dialogue]

        created_at = db_obj.created_at
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        updated_at = db_obj.updated_at
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        return TeachingSessionModel(
            session_id=db_obj.id,
            user_id=db_obj.user_id,
            topic=db_obj.topic,
            subject=db_obj.subject or "General",
            document_id=db_obj.document_id,
            document_name=db_obj.document_name,
            current_state=state,
            current_step_index=db_obj.current_step_index,
            steps=steps,
            dialogue=dialogue,
            struggle_count=db_obj.struggle_count,
            mastery_score=db_obj.mastery_score,
            is_completed=db_obj.is_completed,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def _dump_steps(steps: List[ConceptStep]) -> List[Dict[str, Any]]:
        result = []
        for s in steps:
            if hasattr(s, "model_dump"):
                result.append(s.model_dump())
            elif hasattr(s, "dict"):
                result.append(s.dict())
            elif isinstance(s, dict):
                result.append(s)
        return result

    @staticmethod
    def _dump_dialogue(dialogue: List[StudentDialogueTurn]) -> List[Dict[str, Any]]:
        result = []
        for d in dialogue:
            if hasattr(d, "model_dump"):
                result.append(d.model_dump())
            elif hasattr(d, "dict"):
                result.append(d.dict())
            elif isinstance(d, dict):
                result.append(d)
        return result

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        session: TeachingSessionModel,
    ) -> TeachingSessionModel:
        """Persists a new teaching session to the database."""
        state_str = (
            session.current_state.value
            if isinstance(session.current_state, TeachingState)
            else str(session.current_state)
        )

        db_session = TeachingSessionDB(
            id=session.session_id,
            user_id=session.user_id,
            topic=session.topic,
            subject=session.subject or "General",
            document_id=session.document_id,
            document_name=session.document_name,
            current_state=state_str,
            current_step_index=session.current_step_index,
            steps=cls._dump_steps(session.steps),
            dialogue=cls._dump_dialogue(session.dialogue),
            struggle_count=session.struggle_count,
            mastery_score=session.mastery_score,
            is_completed=session.is_completed,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        return cls._to_pydantic(db_session)

    @classmethod
    async def get_session(
        cls,
        db: AsyncSession,
        session_id: str,
    ) -> Optional[TeachingSessionModel]:
        """Fetches a teaching session by primary key ID."""
        stmt = select(TeachingSessionDB).where(TeachingSessionDB.id == session_id)
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        return cls._to_pydantic(db_obj)

    @classmethod
    async def save_session(
        cls,
        db: AsyncSession,
        session: TeachingSessionModel,
    ) -> TeachingSessionModel:
        """Upserts/updates an existing teaching session."""
        stmt = select(TeachingSessionDB).where(TeachingSessionDB.id == session.session_id)
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        state_str = (
            session.current_state.value
            if isinstance(session.current_state, TeachingState)
            else str(session.current_state)
        )
        steps_json = cls._dump_steps(session.steps)
        dialogue_json = cls._dump_dialogue(session.dialogue)

        if not db_obj:
            db_obj = TeachingSessionDB(
                id=session.session_id,
                user_id=session.user_id,
                topic=session.topic,
                subject=session.subject or "General",
                document_id=session.document_id,
                document_name=session.document_name,
                current_state=state_str,
                current_step_index=session.current_step_index,
                steps=steps_json,
                dialogue=dialogue_json,
                struggle_count=session.struggle_count,
                mastery_score=session.mastery_score,
                is_completed=session.is_completed,
                created_at=session.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(db_obj)
        else:
            db_obj.topic = session.topic
            db_obj.subject = session.subject or "General"
            db_obj.document_id = session.document_id
            db_obj.document_name = session.document_name
            db_obj.current_state = state_str
            db_obj.current_step_index = session.current_step_index
            db_obj.steps = steps_json
            db_obj.dialogue = dialogue_json
            db_obj.struggle_count = session.struggle_count
            db_obj.mastery_score = session.mastery_score
            db_obj.is_completed = session.is_completed
            db_obj.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(db_obj)
        return cls._to_pydantic(db_obj)

    @classmethod
    async def get_active_sessions_for_user(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> List[TeachingSessionModel]:
        """Returns all non-completed sessions for a user."""
        stmt = select(TeachingSessionDB).where(
            TeachingSessionDB.user_id == user_id,
            TeachingSessionDB.is_completed == False,
        ).order_by(TeachingSessionDB.updated_at.desc())
        result = await db.execute(stmt)
        return [cls._to_pydantic(row) for row in result.scalars().all()]

    @classmethod
    async def cleanup_stale_sessions(
        cls,
        db: AsyncSession,
        older_than_hours: int = 24,
    ) -> int:
        """
        Deletes incomplete/stale sessions older than `older_than_hours`
        to prevent database bloat.
        Returns number of deleted rows.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        # Using datetime directly is supported by SQLAlchemy
        stmt = delete(TeachingSessionDB).where(
            and_(
                TeachingSessionDB.updated_at < cutoff,
                TeachingSessionDB.is_completed == False,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

    @classmethod
    async def rehydrate_active_sessions(
        cls,
        db: AsyncSession,
        limit: int = 100,
    ) -> Dict[str, TeachingSessionModel]:
        """
        Loads uncompleted, recent active sessions from the DB
        to populate the in-memory cache upon application startup.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = select(TeachingSessionDB).where(
            and_(
                TeachingSessionDB.updated_at >= cutoff,
                TeachingSessionDB.is_completed == False,
            )
        ).order_by(TeachingSessionDB.updated_at.desc()).limit(limit)

        result = await db.execute(stmt)
        rehydrated: Dict[str, TeachingSessionModel] = {}
        for row in result.scalars().all():
            model = cls._to_pydantic(row)
            rehydrated[model.session_id] = model

        # Update the module-level active session cache in engine.py
        from app.teaching.engine import _active_sessions
        _active_sessions.update(rehydrated)
        return rehydrated
