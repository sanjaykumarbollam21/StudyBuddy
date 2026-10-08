from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.user import User, Profile, UserSettings, Notification

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.profile), selectinload(User.settings))
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.profile), selectinload(User.settings))
            .where(User.email == email.lower())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, email: str, hashed_password: str, full_name: Optional[str] = None) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_verified=False
        )
        self.db.add(user)
        await self.db.flush()

        # Automatically create initial Profile and Settings
        profile = Profile(user_id=user.id)
        settings = UserSettings(user_id=user.id)
        self.db.add(profile)
        self.db.add(settings)
        
        # Add welcome notification
        welcome_note = Notification(
            user_id=user.id,
            title="Welcome to Study Buddy! 🎓",
            message="Your AI personal teacher is ready. Start by exploring topics or setting your study preferences.",
            notification_type="reminder"
        )
        self.db.add(welcome_note)

        await self.db.commit()
        await self.db.refresh(user)
        return await self.get_by_id(user.id)

    async def update_profile(self, user_id: str, **kwargs) -> Optional[Profile]:
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            profile = Profile(user_id=user_id)
            self.db.add(profile)

        for key, value in kwargs.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_settings(self, user_id: str, **kwargs) -> Optional[UserSettings]:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)

        for key, value in kwargs.items():
            if value is not None and hasattr(settings, key):
                setattr(settings, key, value)

        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def get_notifications(self, user_id: str, limit: int = 20) -> List[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
