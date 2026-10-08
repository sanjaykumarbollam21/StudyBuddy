from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import SignUpRequest, LoginRequest, TokenResponse, PasswordResetRequest, MessageResponse
from app.schemas.user import UserResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """Register a new student account and return JWT access token."""
    service = AuthService(db)
    return await service.register(request)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate student with email & password, returning JWT access token."""
    service = AuthService(db)
    return await service.authenticate(request)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get profile and settings for the currently authenticated student."""
    return UserResponse.model_validate(current_user)

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Initiate password reset for a registered student."""
    # In production, this emails a secure one-time token.
    # For dev/sandbox, return a confirmation message.
    return MessageResponse(
        message=f"If an account exists for {request.email}, password reset instructions have been dispatched.",
        success=True
    )
