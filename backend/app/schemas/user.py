from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class ProfileBase(BaseModel):
    education_level: Optional[str] = None
    target_goals: Optional[str] = None
    preferred_study_duration_mins: Optional[int] = 45
    daily_available_mins: Optional[int] = 120
    learning_style: Optional[str] = "visual_practical"
    current_knowledge_level: Optional[str] = "beginner"
    upcoming_exam_date: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class ProfileUpdate(BaseModel):
    education_level: Optional[str] = None
    target_goals: Optional[str] = None
    preferred_study_duration_mins: Optional[int] = Field(default=None, ge=10, le=360)
    daily_available_mins: Optional[int] = Field(default=None, ge=10, le=720)
    learning_style: Optional[str] = None
    current_knowledge_level: Optional[str] = None
    upcoming_exam_date: Optional[datetime] = None
    bio: Optional[str] = None

class ProfileResponse(ProfileBase):
    user_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserSettingsBase(BaseModel):
    theme: Optional[str] = "system"
    ai_provider: Optional[str] = "gemini"
    voice_speed: Optional[float] = 1.0
    voice_type: Optional[str] = "alloy"
    allow_email_notifications: Optional[bool] = True
    allow_study_reminders: Optional[bool] = True
    auto_generate_quizzes: Optional[bool] = True
    spaced_repetition_enabled: Optional[bool] = True

class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    ai_provider: Optional[str] = None
    voice_speed: Optional[float] = None
    voice_type: Optional[str] = None
    allow_email_notifications: Optional[bool] = None
    allow_study_reminders: Optional[bool] = None
    auto_generate_quizzes: Optional[bool] = None
    spaced_repetition_enabled: Optional[bool] = None

class UserSettingsResponse(UserSettingsBase):
    user_id: str
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: Optional[ProfileResponse] = None
    settings: Optional[UserSettingsResponse] = None
    model_config = ConfigDict(from_attributes=True)

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
