from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class GroundingMode(str, Enum):
    STRICT_MATERIALS = "strict_materials"
    MATERIALS_PLUS_GENERAL = "materials_plus_general"
    GENERAL = "general"

class SourceCitation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_id: Optional[str] = None
    similarity_score: Optional[float] = None

class TutorAskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Student's question or teaching prompt")
    document_ids: Optional[List[str]] = Field(None, description="Scope answer to specific documents")
    subject: Optional[str] = Field(None, description="Scope answer to a specific subject track")
    collection: Optional[str] = Field(None, description="Scope answer to a specific collection")
    grounding_mode: Optional[GroundingMode] = Field(
        GroundingMode.MATERIALS_PLUS_GENERAL,
        description="Grounding policy (strict_materials, materials_plus_general, general)"
    )
    session_id: Optional[str] = None

class TutorAskResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = []
    grounding_mode: GroundingMode
    context_used: bool = False
    session_id: Optional[str] = None

class DocumentSessionResponse(BaseModel):
    document_id: str
    document_name: str
    session_id: str
    welcome_message: str
    suggested_topics: List[str] = []
