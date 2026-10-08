from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.sync import SyncPushRequest, SyncPushResponse, SyncPullResponse
from app.sync.service import SyncEngine

router = APIRouter(prefix="/sync", tags=["Offline-First Synchronization Engine"])


class PullRequestPayload(BaseModel):
    device_id: str
    since_timestamp: Optional[datetime] = None


@router.post("/push", response_model=SyncPushResponse)
async def push_sync_changes(
    request: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Push offline client changes with deterministic conflict resolution.
    Updates learning mastery, revision items, and study plans.
    """
    engine = SyncEngine(db_session=db)
    return await engine.push_changes(
        user_id=current_user.id,
        device_id=request.device_id,
        changes=request.changes,
    )


@router.post("/pull", response_model=SyncPullResponse)
async def pull_sync_changes(
    request: PullRequestPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pull updates from the server since the client's last synchronization watermark.
    """
    engine = SyncEngine(db_session=db)
    return await engine.pull_changes(
        user_id=current_user.id,
        device_id=request.device_id,
        since_timestamp=request.since_timestamp,
    )
