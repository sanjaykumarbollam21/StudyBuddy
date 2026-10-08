import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_type = Column(String(50), nullable=False) # pdf, docx, txt, md
    file_size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=True) # backward compatibility
    
    # Processing state machine: UPLOADING -> UPLOADED -> PROCESSING -> EXTRACTING -> CLEANING -> CHUNKING -> INDEXING -> READY (or FAILED)
    status = Column(String(50), default="ready")
    processing_status = Column(String(50), default="ready") # backward compatibility
    processing_stage = Column(String(50), default="ready")
    progress = Column(Integer, default=100) # 0 to 100
    processing_progress = Column(Integer, default=100) # backward compatibility
    error_message = Column(Text, nullable=True)

    # Document Metrics
    page_count = Column(Integer, default=1)
    extracted_character_count = Column(Integer, default=0)
    section_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    
    # Phase 3 Embedding Tracking
    embedding_status = Column(String(50), default="ready") # pending, processing, ready, failed
    embedding_model = Column(String(100), nullable=True, default="local-neural-hash-384")
    embedding_dimension = Column(Integer, nullable=True, default=384)
    embedded_at = Column(DateTime, nullable=True)
    embedding_error = Column(Text, nullable=True)

    subject_name = Column(String(150), nullable=True, default="General")
    collection_name = Column(String(150), nullable=True, default="My Materials")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_doc_chunk", "document_id", "chunk_index"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(255), nullable=True)
    character_start = Column(Integer, nullable=True, default=0)
    character_end = Column(Integer, nullable=True, default=0)
    
    # Phase 3 Vector Embedding Storage
    embedding = Column(JSON, nullable=True) # Stores List[float] embedding vector
    embedding_model = Column(String(100), nullable=True)
    embedded_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="chunks")
