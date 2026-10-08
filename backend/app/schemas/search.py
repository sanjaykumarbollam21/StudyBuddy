from typing import List, Optional
from pydantic import BaseModel, Field

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    top_k: int = Field(8, ge=1, le=50, description="Maximum number of results to retrieve")
    document_ids: Optional[List[str]] = Field(None, description="Scope search to specific document IDs")
    subject: Optional[str] = Field(None, description="Scope search to a specific subject track")
    collection: Optional[str] = Field(None, description="Scope search to a specific collection")

class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    top_k: int = Field(8, ge=1, le=50, description="Maximum number of results to retrieve")
    document_ids: Optional[List[str]] = Field(None, description="Scope search to specific document IDs")
    subject: Optional[str] = Field(None, description="Scope search to a specific subject track")
    collection: Optional[str] = Field(None, description="Scope search to a specific collection")
    alpha: float = Field(0.7, ge=0.0, le=1.0, description="Weight between vector (1.0) and lexical keyword (0.0)")

class SearchResultChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    similarity: float = Field(..., description="Relevance / similarity score (0.0 to 1.0)")
    score_type: Optional[str] = "semantic" # semantic, keyword, hybrid

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultChunk]
