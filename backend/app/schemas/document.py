from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    character_start: Optional[int] = 0
    character_end: Optional[int] = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: Optional[str] = None
    file_type: str
    file_size_bytes: int
    page_count: int = 1
    extracted_character_count: int = 0
    section_count: int = 0
    chunk_count: int = 0
    subject_name: Optional[str] = "General"
    collection_name: Optional[str] = "My Materials"
    status: str
    processing_stage: Optional[str] = "ready"
    progress: int = 100
    error_message: Optional[str] = None
    
    # Phase 3 Embedding Metadata
    embedding_status: Optional[str] = "ready"
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    embedded_at: Optional[datetime] = None
    embedding_error: Optional[str] = None

    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    progress: int
    stage: str
    message: str
    embedding_status: Optional[str] = "ready"

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []
    preview_text: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class BulkDeleteRequest(BaseModel):
    document_ids: List[str]

class DocumentDeleteResponse(BaseModel):
    success: bool
    deleted_count: int
    message: str

class DocumentRetryResponse(BaseModel):
    document_id: str
    status: str
    message: str

class DocumentReindexResponse(BaseModel):
    document_id: str
    status: str
    chunks_embedded: int
    model: str
    dimension: int
    message: str

class LearningFromDocResponse(BaseModel):
    document_id: str
    status: str = "curriculum_queued"
    message: str
    recommended_action: str = "Curriculum and adaptive roadmap generation will be completed in Phase 3/5."
