from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Index
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class SyncChange(Base):
    """
    Audit log / change record of mutations for offline-first bidirectional synchronization.
    Tracks inserts, updates, and deletes with client and server timestamps.
    """
    __tablename__ = "sync_changes"
    __table_args__ = (
        Index("ix_sync_changes_user_time", "user_id", "server_timestamp"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # mastery, revision_item, study_plan_item, user_settings
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # create, update, delete
    client_timestamp = Column(DateTime, nullable=False, default=utc_now)
    server_timestamp = Column(DateTime, nullable=False, default=utc_now, index=True)
    payload = Column(JSON, default=dict)
    version = Column(Integer, default=1)


class DeviceSyncState(Base):
    """
    Tracks client device sync watermarks for delta downloads.
    """
    __tablename__ = "device_sync_states"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False)
    last_synced_at = Column(DateTime, nullable=False, default=utc_now)
    sync_cursor = Column(Integer, default=0)
