from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class SyncChangeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str  # mastery, revision_item, study_plan_item, user_settings
    entity_id: str
    action: str  # create, update, delete
    client_timestamp: datetime
    server_timestamp: Optional[datetime] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1


class SyncPushRequest(BaseModel):
    device_id: str
    changes: List[SyncChangeItem]


class SyncPushResponse(BaseModel):
    success: bool = True
    applied_count: int
    conflict_count: int = 0
    server_timestamp: datetime


class SyncPullResponse(BaseModel):
    server_timestamp: datetime
    changes: List[SyncChangeItem] = []
    has_more: bool = False
