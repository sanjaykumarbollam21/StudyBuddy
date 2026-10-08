from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.search import (
    SemanticSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    SearchResultChunk,
)
from app.repositories.vector_repository import VectorRepository
from app.embeddings import get_embedding_provider
from app.search.hybrid import KnowledgeSearchService

router = APIRouter(prefix="/search", tags=["Semantic Search & Knowledge Base"])

def get_search_service(db: AsyncSession = Depends(get_db)) -> KnowledgeSearchService:
    vector_repo = VectorRepository(db)
    embedding_provider = get_embedding_provider()
    return KnowledgeSearchService(vector_repo, embedding_provider)

@router.post("/semantic", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    search_service: KnowledgeSearchService = Depends(get_search_service),
):
    """
    Search student's personal knowledge base using dense vector cosine similarity.
    Strict tenant isolation: Only returns chunks belonging to current_user.
    """
    results = await search_service.search_semantic(
        user_id=current_user.id,
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids,
        subject=request.subject,
        collection=request.collection,
    )

    chunks = [
        SearchResultChunk(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            document_name=r["document_name"],
            content=r["content"],
            page_number=r.get("page_number"),
            section_title=r.get("section_title"),
            similarity=r["similarity"],
            score_type=r.get("score_type", "semantic"),
        )
        for r in results
    ]

    return SearchResponse(
        query=request.query,
        total_results=len(chunks),
        results=chunks,
    )

@router.post("/hybrid", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def hybrid_search(
    request: HybridSearchRequest,
    current_user: User = Depends(get_current_user),
    search_service: KnowledgeSearchService = Depends(get_search_service),
):
    """
    Hybrid search combining vector semantic similarity with lexical keyword matching
    and result diversification.
    """
    results = await search_service.search_hybrid(
        user_id=current_user.id,
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids,
        subject=request.subject,
        collection=request.collection,
        alpha=request.alpha,
    )

    chunks = [
        SearchResultChunk(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            document_name=r["document_name"],
            content=r["content"],
            page_number=r.get("page_number"),
            section_title=r.get("section_title"),
            similarity=r["similarity"],
            score_type=r.get("score_type", "hybrid"),
        )
        for r in results
    ]

    return SearchResponse(
        query=request.query,
        total_results=len(chunks),
        results=chunks,
    )
