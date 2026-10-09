from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.tutor import router as tutor_router
from app.api.teaching import router as teaching_router
from app.api.curriculum import router as curriculum_router
from app.api.practice import router as practice_router
from app.api.revision import router as revision_router
from app.api.exam import router as exam_router
from app.api.voice import router as voice_router
from app.api.planner import router as planner_router
from app.api.sync import router as sync_router
from app.api.notifications import router as notifications_router
from app.api.settings import router as settings_router
from app.api.agent import router as agent_router
from app.api.competitive_exams import router as competitive_exams_router
from app.core.telemetry import StructuredLoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Rehydrate active teaching sessions and cleanup stale sessions (>24 hours)
    try:
        async with AsyncSessionLocal() as db_sess:
            from app.teaching.service import TeachingSessionService
            await TeachingSessionService.cleanup_stale_sessions(db_sess, older_than_hours=24)
            await TeachingSessionService.rehydrate_active_sessions(db_sess)
    except Exception:
        pass

    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Study Buddy Backend API - Personal AI Teacher",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)

# Exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        # In debug mode, provide error info for development
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error": str(exc)},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# Include Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(tutor_router, prefix=settings.API_V1_STR)
app.include_router(teaching_router, prefix=settings.API_V1_STR)
app.include_router(curriculum_router, prefix=settings.API_V1_STR)
app.include_router(practice_router, prefix=settings.API_V1_STR)
app.include_router(revision_router, prefix=settings.API_V1_STR)
app.include_router(exam_router, prefix=settings.API_V1_STR)
app.include_router(voice_router, prefix=settings.API_V1_STR)
app.include_router(planner_router, prefix=settings.API_V1_STR)
app.include_router(sync_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(agent_router, prefix=settings.API_V1_STR)
app.include_router(competitive_exams_router, prefix=settings.API_V1_STR)




@app.get("/")
async def root():
    return {
        "message": "Welcome to Study Buddy API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, workers=1, reload=settings.DEBUG and settings.ENVIRONMENT == "development")
