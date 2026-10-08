from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.tutor import (
    TutorAskRequest,
    TutorAskResponse,
    DocumentSessionResponse,
)
from app.repositories.vector_repository import VectorRepository
from app.embeddings import get_embedding_provider
from app.search.hybrid import KnowledgeSearchService
from app.tutor.service import TutorService

router = APIRouter(prefix="/tutor", tags=["AI Teacher & RAG Tutoring"])

def get_tutor_service(db: AsyncSession = Depends(get_db)) -> TutorService:
    vector_repo = VectorRepository(db)
    embedding_provider = get_embedding_provider()
    search_service = KnowledgeSearchService(vector_repo, embedding_provider)
    return TutorService(session=db, search_service=search_service)

@router.post("/ask", response_model=TutorAskResponse, status_code=status.HTTP_200_OK)
async def ask_ai_teacher(
    request: TutorAskRequest,
    current_user: User = Depends(get_current_user),
    tutor_service: TutorService = Depends(get_tutor_service),
):
    """
    Ask Study Buddy a question.
    Grounded in the student's uploaded materials using semantic retrieval.
    Returns answer with structured source citations.
    """
    return await tutor_service.ask_tutor(
        user_id=current_user.id,
        request=request,
    )

@router.post("/document-session/{document_id}", response_model=DocumentSessionResponse, status_code=status.HTTP_200_OK)
async def start_document_teaching_session(
    document_id: str,
    current_user: User = Depends(get_current_user),
    tutor_service: TutorService = Depends(get_tutor_service),
):
    """
    'Teach Me This': Initiates a dedicated teaching session scoped to the selected document.
    """
    try:
        return await tutor_service.start_document_session(
            document_id=document_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
