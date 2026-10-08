from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid


class NotificationItem:
    def __init__(
        self,
        id: str,
        user_id: str,
        title: str,
        message: str,
        category: str,  # session_kickoff, revision_due, exam_alert, system
        action_route: Optional[str] = None,
        created_at: Optional[datetime] = None,
        is_read: bool = False,
        priority: str = "medium",  # low, medium, high, urgent
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.message = message
        self.category = category
        self.action_route = action_route
        self.created_at = created_at or datetime.now(timezone.utc)
        self.is_read = is_read
        self.priority = priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "action_route": self.action_route,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_read": self.is_read,
            "priority": self.priority,
        }


class NotificationService:
    """
    In-memory and DB-backed notification service for proactive study alerts,
    session start reminders, revision deadlines, and exam countdowns.
    """

    def __init__(self):
        # In-memory storage for active session alerts
        self._notifications: Dict[str, List[NotificationItem]] = {}

    def get_user_notifications(self, user_id: str) -> List[NotificationItem]:
        return self._notifications.get(user_id, [])

    def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        items = self._notifications.get(user_id, [])
        for item in items:
            if item.id == notification_id:
                item.is_read = True
                return True
        return False

    def add_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        category: str,
        action_route: Optional[str] = None,
        priority: str = "medium",
    ) -> NotificationItem:
        item = NotificationItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            action_route=action_route,
            priority=priority,
        )
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].insert(0, item)
        return item

    def generate_proactive_study_notifications(
        self,
        user_id: str,
        current_topic_name: Optional[str] = "Operating Systems",
        session_duration_minutes: int = 30,
        due_revision_count: int = 0,
        exam_name: Optional[str] = None,
        days_until_exam: Optional[int] = None,
        weak_topic_name: Optional[str] = None,
    ) -> List[NotificationItem]:
        """
        Generates production-grade proactive notifications:
        - Study session kickoff
        - Due spaced revision items
        - Exam countdown & weak topic warning
        """
        generated: List[NotificationItem] = []

        # 1. Session Kickoff Notification
        if current_topic_name:
            n1 = self.add_notification(
                user_id=user_id,
                title="Study Session Kickoff",
                message=f"Your {session_duration_minutes}-minute study session is starting. Ready to continue {current_topic_name}?",
                category="session_kickoff",
                action_route="/teaching",
                priority="high",
            )
            generated.append(n1)

        # 2. Spaced Revision Due
        if due_revision_count > 0:
            n2 = self.add_notification(
                user_id=user_id,
                title="Revision Due",
                message=f"You have {due_revision_count} revision item{'s' if due_revision_count > 1 else ''} due today.",
                category="revision_due",
                action_route="/revision",
                priority="medium",
            )
            generated.append(n2)

        # 3. Exam Proximity Alert
        if exam_name and days_until_exam is not None:
            msg = f"Your {exam_name} exam is {days_until_exam} days away."
            if weak_topic_name:
                msg += f" {weak_topic_name} is still below your target mastery."
            n3 = self.add_notification(
                user_id=user_id,
                title="Exam Countdown Alert",
                message=msg,
                category="exam_alert",
                action_route="/exam",
                priority="urgent" if days_until_exam <= 5 else "high",
            )
            generated.append(n3)

        return generated


notification_service = NotificationService()
