from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.document_service import DocumentService
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentStatusResponse,
    DocumentDeleteResponse,
    DocumentRetryResponse,
    DocumentReindexResponse,
    BulkDeleteRequest,
    LearningFromDocResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents & Knowledge Base"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    subject_name: Optional[str] = Form("General"),
    collection_name: Optional[str] = Form("My Materials"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload study material (PDF, DOCX, TXT, Markdown).
    Validates file format, size, and content.
    Extracts structure, chunks semantically, and stores permanently.
    """
    service = DocumentService(db)
    return await service.upload_and_initiate_processing(
        user_id=current_user.id,
        upload_file=file,
        subject_name=subject_name,
        collection_name=collection_name,
    )

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: all, processing, ready, failed"),
    subject: Optional[str] = Query(None, description="Filter by subject track"),
    search: Optional[str] = Query(None, description="Search by filename, subject or collection"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all saved study materials for the authenticated student."""
    service = DocumentService(db)
    return await service.list_documents(
        user_id=current_user.id,
        status_filter=status_filter,
        subject_filter=subject,
        search_query=search,
    )

@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full document metrics, chunk sections, and text preview."""
    service = DocumentService(db)
    return await service.get_document_details(document_id=document_id, user_id=current_user.id)

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check live processing status, progress percentage, and active stage."""
    service = DocumentService(db)
    return await service.get_document_status(document_id=document_id, user_id=current_user.id)

@router.post("/{document_id}/retry", response_model=DocumentRetryResponse)
async def retry_document_processing(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry extraction and chunking pipeline on a failed document."""
    service = DocumentService(db)
    return await service.retry_document_processing(document_id=document_id, user_id=current_user.id)

@router.post("/{document_id}/reindex", response_model=DocumentReindexResponse)
async def reindex_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-generate dense vector embeddings for all chunks in the document."""
    from app.documents.processor import DocumentProcessor
    from app.embeddings import get_embedding_provider
    try:
        count = await DocumentProcessor.reindex_document(
            document_id=document_id,
            user_id=current_user.id,
            session=db,
        )
        provider = get_embedding_provider()
        return DocumentReindexResponse(
            document_id=document_id,
            status="ready",
            chunks_embedded=count,
            model=provider.get_model_name(),
            dimension=provider.get_dimension(),
            message=f"Successfully re-indexed {count} chunks.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an unnecessary document, its chunks, and its stored physical file."""
    service = DocumentService(db)
    return await service.delete_document(document_id=document_id, user_id=current_user.id)

@router.post("/bulk-delete", response_model=DocumentDeleteResponse)
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple selected unnecessary documents in a single atomic request."""
    service = DocumentService(db)
    return await service.bulk_delete_documents(
        document_ids=request.document_ids,
        user_id=current_user.id,
    )

@router.post("/learning/from-document/{document_id}", response_model=LearningFromDocResponse)
async def learn_from_document_contract(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Contract endpoint preparing for AI Teacher curriculum generation from this document."""
    service = DocumentService(db)
    # Verify ownership
    await service.get_document_details(document_id=document_id, user_id=current_user.id)
    return LearningFromDocResponse(
        document_id=document_id,
        status="curriculum_queued",
        message="Document verified. Curriculum roadmap generation will be activated in Phase 3/5.",
    )
