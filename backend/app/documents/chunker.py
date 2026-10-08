import uuid
from typing import List, Optional
from app.models.document import DocumentChunk
from app.documents.extractors.base import ExtractedSection

class ChunkingService:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        document_id: str,
        user_id: str,
        text: str,
        total_pages: int = 1,
        sections: Optional[List[ExtractedSection]] = None,
    ) -> List[DocumentChunk]:
        if not text:
            return []

        chunks: List[DocumentChunk] = []
        step = max(50, self.chunk_size - self.chunk_overlap)
        start = 0
        chunk_idx = 0

        total_len = len(text)
        sections = sections or []

        while start < total_len:
            end = min(start + self.chunk_size, total_len)

            # Try to avoid breaking in the middle of a sentence if possible
            if end < total_len:
                last_period = text.rfind(".", start + 200, end)
                last_newline = text.rfind("\n", start + 200, end)
                break_point = max(last_period, last_newline)
                if break_point > start:
                    end = break_point + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                # Determine page number based on character position
                progress_fraction = start / max(1, total_len)
                estimated_page = min(total_pages, int(progress_fraction * total_pages) + 1)

                # Determine current active section
                current_section = "General Overview"
                for sec in sections:
                    if sec.character_start <= start <= sec.character_end:
                        current_section = sec.title
                        break

                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    user_id=user_id,
                    chunk_index=chunk_idx,
                    content=chunk_text,
                    page_number=estimated_page,
                    section_title=current_section,
                    character_start=start,
                    character_end=end,
                )
                chunks.append(chunk)
                chunk_idx += 1

            start += step

        return chunks
