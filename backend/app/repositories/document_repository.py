from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.document import Document, DocumentChunk

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(
        self,
        user_id: str,
        filename: str,
        original_filename: str,
        mime_type: str,
        file_type: str,
        file_size_bytes: int,
        storage_path: str,
        page_count: int = 1,
        subject_name: Optional[str] = "General",
        collection_name: Optional[str] = "My Materials",
        status: str = "uploaded",
        processing_stage: str = "uploaded",
        progress: int = 5,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            storage_path=storage_path,
            file_path=storage_path,
            page_count=page_count,
            subject_name=subject_name or "General",
            collection_name=collection_name or "My Materials",
            status=status,
            processing_status=status,
            processing_stage=processing_stage,
            progress=progress,
            processing_progress=progress,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_documents(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        subject_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Document]:
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        if status_filter and status_filter.lower() != "all":
            stmt = stmt.where(Document.status == status_filter.lower())
        if subject_filter:
            stmt = stmt.where(Document.subject_name == subject_filter)
        if search_query:
            term = f"%{search_query.lower()}%"
            stmt = stmt.where(
                (Document.filename.ilike(term))
                | (Document.subject_name.ilike(term))
                | (Document.collection_name.ilike(term))
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, document_id: str, user_id: str) -> Optional[Document]:
        stmt = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id, Document.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: str, user_id: str) -> Optional[Document]:
        doc = await self.get_by_id(document_id, user_id)
        if not doc:
            return None
        await self.db.delete(doc)
        await self.db.commit()
        return doc

    async def bulk_delete_documents(self, document_ids: List[str], user_id: str) -> List[Document]:
        stmt = (
            select(Document)
            .where(Document.id.in_(document_ids), Document.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        docs = list(result.scalars().all())
        for doc in docs:
            await self.db.delete(doc)
        if docs:
            await self.db.commit()
        return docs
