import os
from typing import List, Union
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Study Buddy API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "development-secret-key-study-buddy-32-chars-min-needed-here-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./study_buddy.db"
    DB_ECHO: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5000",
        "http://localhost",
        "*"
    ]
    
    # AI Modes & Providers (Cloud-First Architecture)
    AI_MODE: str = "cloud" # cloud, test
    OFFLINE_ONLY: bool = False
    AI_DEFAULT_PROVIDER: str = "gemini" # gemini, openai, mock
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    AI_REQUEST_TIMEOUT_SECONDS: float = 30.0
    AI_MAX_RETRIES: int = 3
    AI_RETRY_BACKOFF_FACTOR: float = 1.5
    
    # Embedding Configuration (Phase 3.1)
    EMBEDDING_PROVIDER: str = "local" # local, gemini, openai
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 16
    VECTOR_DISTANCE: str = "cosine" # cosine, l2, inner_product
    
    # RAG & Grounding Configuration
    DEFAULT_GROUNDING_MODE: str = "materials_plus_general" # strict_materials, materials_plus_general, general
    SIMILARITY_THRESHOLD: float = 0.40
    MAX_RAG_CHUNKS: int = 8
    
    # Storage
    STORAGE_TYPE: str = "local" # local, supabase
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Supabase (Auth, Storage & Cloud Services)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_BUCKET: str = "study-materials"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
