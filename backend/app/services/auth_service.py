from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import SignUpRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse, ProfileUpdate, UserSettingsUpdate
from app.models.user import User

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, request: SignUpRequest) -> TokenResponse:
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )
        
        hashed_password = get_password_hash(request.password)
        user = await self.user_repo.create_user(
            email=request.email,
            hashed_password=hashed_password,
            full_name=request.full_name
        )

        token = create_access_token(subject=user.id)
        user_response = UserResponse.model_validate(user)
        return TokenResponse(access_token=token, token_type="bearer", user=user_response)

    async def authenticate(self, request: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been disabled."
            )

        token = create_access_token(subject=user.id)
        user_response = UserResponse.model_validate(user)
        return TokenResponse(access_token=token, token_type="bearer", user=user_response)

    async def get_user_profile(self, user_id: str) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: str, profile_in: ProfileUpdate) -> UserResponse:
        await self.user_repo.update_profile(
            user_id=user_id,
            **profile_in.model_dump(exclude_unset=True)
        )
        return await self.get_user_profile(user_id)

    async def update_settings(self, user_id: str, settings_in: UserSettingsUpdate) -> UserResponse:
        await self.user_repo.update_settings(
            user_id=user_id,
            **settings_in.model_dump(exclude_unset=True)
        )
        return await self.get_user_profile(user_id)
