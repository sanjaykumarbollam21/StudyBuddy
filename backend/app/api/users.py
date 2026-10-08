from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, ProfileUpdate, UserSettingsUpdate, NotificationResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users & Profile"])

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update student onboarding preferences, education level, and goals."""
    service = AuthService(db)
    return await service.update_profile(current_user.id, profile_in)

@router.put("/settings", response_model=UserResponse)
async def update_settings(
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update student app settings (theme, AI provider, audio speed)."""
    service = AuthService(db)
    return await service.update_settings(current_user.id, settings_in)

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch notifications for the current student."""
    user_repo = UserRepository(db)
    notifications = await user_repo.get_notifications(current_user.id)
    return [NotificationResponse.model_validate(n) for n in notifications]
