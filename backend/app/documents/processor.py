from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document, DocumentChunk
from app.documents.extractors import get_extractor
from app.documents.cleaner import TextCleaner
from app.documents.section_detector import SectionDetector
from app.documents.chunker import ChunkingService
from app.documents.storage import storage_service
from app.embeddings import get_embedding_provider
from app.core.config import settings

class DocumentProcessor:
    @staticmethod
    async def process_document(document_id: str, user_id: str, session: AsyncSession):
        """
        Executes the full Phase 3 document processing & embedding state machine:
        PROCESSING (10%) -> EXTRACTING (25%) -> CLEANING (40%) -> CHUNKING (55%)
        -> EMBEDDING (75%) -> INDEXING (90%) -> READY (100%) (or FAILED).
        Operates within the provided active database session.
        """
        # 1. Fetch document record
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            return

        try:
            # Stage: PROCESSING (10%)
            doc.status = "processing"
            doc.processing_status = "processing"
            doc.processing_stage = "processing"
            doc.progress = 10
            doc.processing_progress = 10
            await session.commit()

            # Read stored file bytes
            file_bytes = storage_service.read_file(doc.storage_path)

            # Stage: EXTRACTING (25%)
            doc.processing_stage = "extracting"
            doc.progress = 25
            doc.processing_progress = 25
            await session.commit()

            extractor = get_extractor(doc.file_type)
            extracted_doc = extractor.extract(file_bytes, filename=doc.filename)

            # Stage: CLEANING (40%)
            doc.processing_stage = "cleaning"
            doc.progress = 40
            doc.processing_progress = 40
            await session.commit()

            cleaned_text = TextCleaner.clean(extracted_doc.text)

            # Stage: CHUNKING (55%)
            doc.processing_stage = "chunking"
            doc.progress = 55
            doc.processing_progress = 55
            await session.commit()

            detected_sections = SectionDetector.detect_sections(cleaned_text)
            if not detected_sections and extracted_doc.sections:
                detected_sections = extracted_doc.sections

            chunker = ChunkingService(chunk_size=700, chunk_overlap=120)
            chunks = chunker.chunk_document(
                document_id=doc.id,
                user_id=doc.user_id,
                text=cleaned_text,
                total_pages=extracted_doc.page_count,
                sections=detected_sections,
            )

            # Stage: EMBEDDING (75%) - Generating dense vector embeddings
            doc.processing_stage = "embedding"
            doc.progress = 75
            doc.processing_progress = 75
            doc.embedding_status = "processing"
            await session.commit()

            embedding_provider = get_embedding_provider()
            model_name = embedding_provider.get_model_name()
            dimension = embedding_provider.get_dimension()
            now = datetime.now(timezone.utc)

            # Batch embedding generation
            batch_size = settings.EMBEDDING_BATCH_SIZE or 16
            chunk_texts = [c.content for c in chunks]

            for i in range(0, len(chunk_texts), batch_size):
                batch_slice = chunk_texts[i:i + batch_size]
                vectors = await embedding_provider.embed_texts(batch_slice)
                for j, vec in enumerate(vectors):
                    chunk_idx = i + j
                    chunks[chunk_idx].embedding = vec
                    chunks[chunk_idx].embedding_model = model_name
                    chunks[chunk_idx].embedded_at = now

            # Stage: INDEXING (90%) - Storing chunks & vectors
            doc.processing_stage = "indexing"
            doc.progress = 90
            doc.processing_progress = 90
            await session.commit()

            # Delete any old chunks (in case of retry)
            del_stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            existing_chunks = (await session.execute(del_stmt)).scalars().all()
            for old_chunk in existing_chunks:
                await session.delete(old_chunk)

            for chunk in chunks:
                session.add(chunk)

            # Stage: READY (100%)
            doc.status = "ready"
            doc.processing_status = "ready"
            doc.processing_stage = "ready"
            doc.progress = 100
            doc.processing_progress = 100
            doc.page_count = extracted_doc.page_count
            doc.extracted_character_count = len(cleaned_text)
            doc.section_count = len(detected_sections)
            doc.chunk_count = len(chunks)
            doc.embedding_status = "ready"
            doc.embedding_model = model_name
            doc.embedding_dimension = dimension
            doc.embedded_at = now
            doc.embedding_error = None
            doc.error_message = None if not extracted_doc.needs_ocr else "NEEDS_OCR: Scanned PDF without selectable text."

            await session.commit()

        except Exception as e:
            await session.rollback()
            doc.status = "failed"
            doc.processing_status = "failed"
            doc.processing_stage = "failed"
            doc.embedding_status = "failed"
            doc.embedding_error = str(e)
            doc.error_message = f"Processing failed: {str(e)}"
            await session.commit()

    @staticmethod
    async def reindex_document(document_id: str, user_id: str, session: AsyncSession) -> int:
        """
        Re-embeds all existing chunks for a document using the currently configured provider.
        Useful when embedding model changes or initial indexing failed.
        """
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Document not found or access denied")

        # Fetch existing chunks
        chunk_stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.user_id == user_id,
        ).order_by(DocumentChunk.chunk_index)
        chunks = (await session.execute(chunk_stmt)).scalars().all()

        if not chunks:
            raise ValueError("No chunks found to re-index")

        doc.embedding_status = "processing"
        await session.commit()

        try:
            provider = get_embedding_provider()
            model_name = provider.get_model_name()
            dimension = provider.get_dimension()
            now = datetime.now(timezone.utc)

            texts = [c.content for c in chunks]
            batch_size = settings.EMBEDDING_BATCH_SIZE or 16

            for i in range(0, len(texts), batch_size):
                batch_slice = texts[i:i + batch_size]
                vectors = await provider.embed_texts(batch_slice)
                for j, vec in enumerate(vectors):
                    c = chunks[i + j]
                    c.embedding = vec
                    c.embedding_model = model_name
                    c.embedded_at = now

            doc.embedding_status = "ready"
            doc.embedding_model = model_name
            doc.embedding_dimension = dimension
            doc.embedded_at = now
            doc.embedding_error = None
            await session.commit()
            return len(chunks)

        except Exception as e:
            doc.embedding_status = "failed"
            doc.embedding_error = str(e)
            await session.commit()
            raise
