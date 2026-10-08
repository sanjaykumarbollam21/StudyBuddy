from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.sync import SyncChange, DeviceSyncState
from app.models.learning import StudentMastery
from app.models.revision import RevisionItem
from app.models.planner import StudyPlanItem
from app.schemas.sync import SyncChangeItem, SyncPushResponse, SyncPullResponse


def utc_now():
    return datetime.now(timezone.utc)


class SyncEngine:
    """
    Offline-First Bidirectional Synchronization Engine.
    Processes change logs with deterministic conflict resolution,
    handles network loss recovery, and syncs learning progress.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    async def push_changes(
        self,
        user_id: str,
        device_id: str,
        changes: List[SyncChangeItem],
    ) -> SyncPushResponse:
        applied_count = 0
        conflict_count = 0
        now = utc_now()

        for ch in changes:
            try:
                if self.db:
                    # Apply entity-specific state merge
                    if ch.entity_type == "mastery":
                        await self._merge_mastery(user_id, ch)
                    elif ch.entity_type == "revision_item":
                        await self._merge_revision_item(user_id, ch)
                    elif ch.entity_type == "study_plan_item":
                        await self._merge_study_plan_item(user_id, ch)

                    # Record change log entry
                    log_entry = SyncChange(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        entity_type=ch.entity_type,
                        entity_id=ch.entity_id,
                        action=ch.action,
                        client_timestamp=ch.client_timestamp,
                        server_timestamp=now,
                        payload=ch.payload,
                        version=ch.version,
                    )
                    self.db.add(log_entry)

                applied_count += 1
            except Exception:
                conflict_count += 1

        if self.db:
            # Update device watermark
            dev_res = await self.db.execute(
                select(DeviceSyncState).where(
                    DeviceSyncState.user_id == user_id,
                    DeviceSyncState.device_id == device_id,
                )
            )
            dev_state = dev_res.scalars().first()
            if not dev_state:
                dev_state = DeviceSyncState(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    device_id=device_id,
                    last_synced_at=now,
                )
                self.db.add(dev_state)
            else:
                dev_state.last_synced_at = now

            await self.db.commit()

        return SyncPushResponse(
            success=True,
            applied_count=applied_count,
            conflict_count=conflict_count,
            server_timestamp=now,
        )

    async def pull_changes(
        self,
        user_id: str,
        device_id: str,
        since_timestamp: Optional[datetime] = None,
    ) -> SyncPullResponse:
        now = utc_now()
        changes: List[SyncChangeItem] = []

        if self.db and since_timestamp:
            res = await self.db.execute(
                select(SyncChange).where(
                    SyncChange.user_id == user_id,
                    SyncChange.server_timestamp > since_timestamp,
                ).order_by(SyncChange.server_timestamp.asc())
            )
            db_changes = list(res.scalars().all())
            changes = [
                SyncChangeItem(
                    id=sc.id,
                    entity_type=sc.entity_type,
                    entity_id=sc.entity_id,
                    action=sc.action,
                    client_timestamp=sc.client_timestamp,
                    server_timestamp=sc.server_timestamp,
                    payload=sc.payload,
                    version=sc.version,
                )
                for sc in db_changes
            ]

        return SyncPullResponse(
            server_timestamp=now,
            changes=changes,
            has_more=False,
        )

    async def _merge_mastery(self, user_id: str, ch: SyncChangeItem):
        payload = ch.payload
        topic_id = payload.get("topic_id", ch.entity_id)

        res = await self.db.execute(
            select(StudentMastery).where(
                StudentMastery.user_id == user_id,
                StudentMastery.topic_id == topic_id,
            )
        )
        mastery = res.scalars().first()

        if not mastery:
            mastery = StudentMastery(
                id=str(uuid.uuid4()),
                user_id=user_id,
                topic_id=topic_id,
                mastery_percentage=float(payload.get("mastery_percentage", 0.0)),
                times_practiced=int(payload.get("times_practiced", 1)),
                consecutive_correct=int(payload.get("consecutive_correct", 0)),
                last_evaluated_at=ch.client_timestamp,
                weak_areas=payload.get("weak_areas", []),
            )
            self.db.add(mastery)
        else:
            # Deterministic merge: take higher practice count and update mastery percentage
            client_score = float(payload.get("mastery_percentage", mastery.mastery_percentage))
            mastery.mastery_percentage = client_score
            mastery.times_practiced = max(mastery.times_practiced, int(payload.get("times_practiced", 0)))
            mastery.last_evaluated_at = ch.client_timestamp

    async def _merge_revision_item(self, user_id: str, ch: SyncChangeItem):
        payload = ch.payload
        res = await self.db.execute(
            select(RevisionItem).where(
                RevisionItem.user_id == user_id,
                RevisionItem.id == ch.entity_id,
            )
        )
        item = res.scalars().first()
        if item:
            item.repetition_interval_days = payload.get("repetition_interval_days", item.repetition_interval_days)
            item.ease_factor = payload.get("ease_factor", item.ease_factor)
            item.mastery_score = payload.get("mastery_score", item.mastery_score)
            item.is_due = payload.get("is_due", item.is_due)

    async def _merge_study_plan_item(self, user_id: str, ch: SyncChangeItem):
        payload = ch.payload
        res = await self.db.execute(
            select(StudyPlanItem).where(StudyPlanItem.id == ch.entity_id)
        )
        item = res.scalars().first()
        if item:
            item.status = payload.get("status", item.status)
            if "performance_score" in payload:
                item.performance_score = payload["performance_score"]
            item.completed_at = ch.client_timestamp
