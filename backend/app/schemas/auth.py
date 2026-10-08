from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=150)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)

class MessageResponse(BaseModel):
    message: str
    success: bool = True
