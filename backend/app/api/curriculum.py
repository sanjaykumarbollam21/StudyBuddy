from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.curriculum.service import CurriculumService
from app.schemas.curriculum import (
    GenerateRoadmapRequest,
    RoadmapResponse,
    NextRecommendationResponse,
    WhyLearningResponse,
)

router = APIRouter(prefix="/curriculum", tags=["Curriculum & Knowledge Graph"])


@router.post("/roadmap/generate", response_model=RoadmapResponse)
async def generate_personalized_roadmap(
    request: GenerateRoadmapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a personalized, DAG-ordered learning roadmap for a subject or document,
    adapting to the student's mastery and prerequisite dependencies.
    """
    try:
        service = CurriculumService(db)
        roadmap = await service.generate_roadmap(
            user_id=current_user.id,
            subject=request.subject,
            goal=request.goal,
            document_id=request.document_id,
        )
        return roadmap
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate curriculum roadmap: {str(e)}",
        )


@router.get("/roadmap/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches a student roadmap with live milestone statuses (locked, unlocked, in_progress, mastered).
    """
    service = CurriculumService(db)
    roadmap = await service.get_roadmap(user_id=current_user.id, roadmap_id=roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning roadmap not found.",
        )
    return roadmap


@router.get("/next", response_model=NextRecommendationResponse)
async def get_next_recommendation(
    roadmap_id: Optional[str] = Query(None, description="Optional roadmap ID filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Answers 'What should I learn next?' by locating the unmastered frontier
    concept whose prerequisites have all been fulfilled.
    """
    try:
        service = CurriculumService(db)
        recommendation = await service.get_next_recommendation(
            user_id=current_user.id,
            roadmap_id=roadmap_id,
        )
        return recommendation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute next recommendation: {str(e)}",
        )


@router.get("/why", response_model=WhyLearningResponse)
async def explain_why_learning(
    topic: str = Query(..., description="Topic or concept title to explain"),
    roadmap_id: Optional[str] = Query(None, description="Optional roadmap ID context"),
    goal: Optional[str] = Query(None, description="Optional student goal context"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Answers 'Why am I learning this?' by bridging prior prerequisites,
    core domain intuition, future unlocks, and student learning goals.
    """
    try:
        service = CurriculumService(db)
        rationale = await service.explain_why_learning(
            user_id=current_user.id,
            topic_title=topic,
            roadmap_id=roadmap_id,
            goal=goal,
        )
        return rationale
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning rationale: {str(e)}",
        )


@router.get("/tracks")
async def list_available_tracks():
    """
    Lists available foundational, offline-capable curriculum tracks.
    """
    return [
        {
            "id": "os",
            "title": "Operating Systems",
            "description": "Kernel architecture, processes, threads, CPU scheduling, synchronization, deadlocks, and virtual memory.",
            "topics_count": 9,
            "difficulty": "intermediate",
            "icon": "desktop_windows",
        },
        {
            "id": "dbms",
            "title": "Database Management Systems",
            "description": "Relational algebra, SQL, normalization (3NF/BCNF), B+ Trees, ACID transactions, and concurrency.",
            "topics_count": 6,
            "difficulty": "intermediate",
            "icon": "storage",
        },
        {
            "id": "ml",
            "title": "Machine Learning",
            "description": "Calculus foundations, linear/logistic regression, regularization, decision trees, and neural networks.",
            "topics_count": 5,
            "difficulty": "intermediate",
            "icon": "psychology",
        },
        {
            "id": "dsa",
            "title": "Python & Data Structures",
            "description": "Asymptotic complexity, linked lists, stacks, queues, binary trees, BST, and graph traversals.",
            "topics_count": 5,
            "difficulty": "beginner",
            "icon": "data_object",
        },
    ]


@router.post("/learning-pack/generate")
async def generate_document_learning_pack(
    document_id: str = Query(..., description="Document ID to generate learning pack from"),
    subject: Optional[str] = Query(None, description="Optional subject override"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Constructs an end-to-end Learning Pack from an uploaded document:
    Knowledge graph DAG, chapters, Socratic lesson plans, and grounded questions.
    """
    try:
        service = CurriculumService(db)
        pack = await service.generate_learning_pack(
            user_id=current_user.id,
            document_id=document_id,
            subject=subject,
        )
        return pack
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document learning pack: {str(e)}",
        )
