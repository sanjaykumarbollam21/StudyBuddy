from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models.user import User
from app.api.deps import get_current_user
from app.notifications.service import notification_service, NotificationItem

router = APIRouter(prefix="/notifications", tags=["Proactive Study Notifications"])


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    category: str
    action_route: Optional[str] = None
    created_at: Optional[str] = None
    is_read: bool
    priority: str


class GenerateNotificationsRequest(BaseModel):
    current_topic_name: Optional[str] = "Operating Systems"
    session_duration_minutes: int = 30
    due_revision_count: int = 0
    exam_name: Optional[str] = None
    days_until_exam: Optional[int] = None
    weak_topic_name: Optional[str] = None


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
):
    """List all proactive study alerts and notifications for the authenticated user."""
    items = notification_service.get_user_notifications(current_user.id)
    return [
        NotificationResponse(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            message=item.message,
            category=item.category,
            action_route=item.action_route,
            created_at=item.created_at.isoformat() if item.created_at else None,
            is_read=item.is_read,
            priority=item.priority,
        )
        for item in items
    ]


@router.post("/generate-proactive", response_model=List[NotificationResponse])
async def generate_proactive_notifications(
    req: GenerateNotificationsRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate study session kickoff, revision due, and exam countdown alerts."""
    items = notification_service.generate_proactive_study_notifications(
        user_id=current_user.id,
        current_topic_name=req.current_topic_name,
        session_duration_minutes=req.session_duration_minutes,
        due_revision_count=req.due_revision_count,
        exam_name=req.exam_name,
        days_until_exam=req.days_until_exam,
        weak_topic_name=req.weak_topic_name,
    )
    return [
        NotificationResponse(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            message=item.message,
            category=item.category,
            action_route=item.action_route,
            created_at=item.created_at.isoformat() if item.created_at else None,
            is_read=item.is_read,
            priority=item.priority,
        )
        for item in items
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    success = notification_service.mark_as_read(current_user.id, notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return {"success": True, "message": "Notification marked as read"}
