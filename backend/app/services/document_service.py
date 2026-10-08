import os
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.repositories.document_repository import DocumentRepository
from app.models.document import Document
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentStatusResponse,
    DocumentDeleteResponse,
    DocumentRetryResponse,
)
from app.documents.storage import storage_service
from app.documents.extractors import SUPPORTED_EXTENSIONS, FUTURE_EXTENSIONS
from app.documents.processor import DocumentProcessor

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)

    async def upload_and_initiate_processing(
        self,
        user_id: str,
        upload_file: UploadFile,
        subject_name: Optional[str] = "General",
        collection_name: Optional[str] = "My Materials",
    ) -> DocumentResponse:
        original_name = upload_file.filename or "unnamed_document"
        
        # 1. Validate file extension
        ext = original_name.split(".")[-1].lower() if "." in original_name else ""
        if not ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File has no extension. Please upload a file with an extension (.pdf, .docx, .txt, .md)."
            )

        if ext in FUTURE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The file format '.{ext}' will be supported in a future version. Currently supported formats: PDF, DOCX, TXT, Markdown."
            )

        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: '.{ext}'. Supported formats are: PDF, DOCX, TXT, and Markdown."
            )

        # 2. Read and validate content size & non-emptiness
        content_bytes = await upload_file.read()
        file_size = len(content_bytes)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty files cannot be processed. Please upload a valid study document."
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"This file exceeds the allowed {settings.MAX_UPLOAD_SIZE_MB} MB limit."
            )

        # 3. Store file securely
        safe_name, storage_path = storage_service.save_file(
            user_id=user_id,
            filename=original_name,
            content=content_bytes,
        )

        # 4. Create document record in database
        doc = await self.doc_repo.create_document(
            user_id=user_id,
            filename=original_name,
            original_filename=original_name,
            mime_type=upload_file.content_type or f"application/{ext}",
            file_type=ext,
            file_size_bytes=file_size,
            storage_path=storage_path,
            subject_name=subject_name,
            collection_name=collection_name,
            status="uploaded",
            processing_stage="uploaded",
            progress=5,
        )

        # 5. Process immediately to ensure fast response / test verification
        await DocumentProcessor.process_document(doc.id, user_id, self.db)
        
        # Refresh to return final status
        refreshed_doc = await self.doc_repo.get_by_id(doc.id, user_id)
        return DocumentResponse.model_validate(refreshed_doc or doc)

    async def list_documents(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        subject_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[DocumentResponse]:
        docs = await self.doc_repo.list_documents(
            user_id=user_id,
            status_filter=status_filter,
            subject_filter=subject_filter,
            search_query=search_query,
        )
        return [DocumentResponse.model_validate(d) for d in docs]

    async def get_document_details(self, document_id: str, user_id: str) -> DocumentDetailResponse:
        doc = await self.doc_repo.get_by_id(document_id, user_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or does not belong to you."
            )
        
        # Build preview text from first chunks
        preview_snippets = [c.content for c in doc.chunks[:3]]
        preview_text = "\n\n...\n\n".join(preview_snippets) if preview_snippets else "No extracted text preview available."

        detail_response = DocumentDetailResponse.model_validate(doc)
        detail_response.preview_text = preview_text
        return detail_response

    async def get_document_status(self, document_id: str, user_id: str) -> DocumentStatusResponse:
        doc = await self.doc_repo.get_by_id(document_id, user_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or does not belong to you."
            )
        
        message_map = {
            "uploaded": "File received and stored securely",
            "processing": "Initiating document processing pipeline",
            "extracting": "Extracting text and page boundaries",
            "cleaning": "Normalizing line endings and cleaning text",
            "chunking": "Splitting content into section-aware chunks",
            "indexing": "Structuring chunks for knowledge base",
            "ready": "Ready for learning and questions",
            "failed": doc.error_message or "Processing failed",
        }
        
        return DocumentStatusResponse(
            document_id=doc.id,
            status=doc.status,
            progress=doc.progress,
            stage=doc.processing_stage,
            message=message_map.get(doc.processing_stage, "Processing document"),
        )

    async def retry_document_processing(self, document_id: str, user_id: str) -> DocumentRetryResponse:
        doc = await self.doc_repo.get_by_id(document_id, user_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or does not belong to you."
            )
        
        doc.status = "processing"
        doc.processing_status = "processing"
        doc.processing_stage = "processing"
        doc.progress = 10
        doc.error_message = None
        await self.db.commit()

        # Re-trigger processing
        await DocumentProcessor.process_document(doc.id, user_id, self.db)

        return DocumentRetryResponse(
            document_id=doc.id,
            status="processing",
            message=f"Reprocessing initiated for '{doc.filename}'.",
        )

    async def delete_document(self, document_id: str, user_id: str) -> DocumentDeleteResponse:
        doc = await self.doc_repo.delete_document(document_id, user_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or does not belong to you."
            )

        storage_service.delete_file(doc.storage_path)

        return DocumentDeleteResponse(
            success=True,
            deleted_count=1,
            message=f"Document '{doc.filename}' was successfully deleted."
        )

    async def bulk_delete_documents(self, document_ids: List[str], user_id: str) -> DocumentDeleteResponse:
        deleted_docs = await self.doc_repo.bulk_delete_documents(document_ids, user_id)
        for doc in deleted_docs:
            storage_service.delete_file(doc.storage_path)

        return DocumentDeleteResponse(
            success=True,
            deleted_count=len(deleted_docs),
            message=f"Successfully deleted {len(deleted_docs)} document(s)."
        )
