from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.schemas.tutor import SourceCitation

# Strict performance limits for LLM context optimization
MAX_RAG_CHUNKS: int = 4
MAX_CONTEXT_TOKENS: int = 1500
MAX_HISTORY_MESSAGES: int = 6
MAX_PROMPT_SIZE: int = 3500

@dataclass
class RAGContext:
    formatted_context: str
    citations: List[SourceCitation]
    retrieved_chunks: List[Dict[str, Any]]
    total_characters: int = 0
    chunk_count: int = 0

class RAGContextBuilder:
    """
    Constructs high-density, cleanly attributed context payloads for LLM tutoring.
    Extracts authentic source citations directly from retrieved chunk metadata.
    Enforces strict context pruning to maximize responsiveness and minimize inference latency.
    """

    def __init__(self, max_context_chars: int = MAX_PROMPT_SIZE, max_chunks: int = MAX_RAG_CHUNKS):
        self.max_context_chars = min(max_context_chars, MAX_PROMPT_SIZE)
        self.max_chunks = max_chunks

    def build_context(self, search_results: List[Dict[str, Any]]) -> RAGContext:
        if not search_results:
            return RAGContext(
                formatted_context="",
                citations=[],
                retrieved_chunks=[],
                total_characters=0,
                chunk_count=0,
            )

        citations: List[SourceCitation] = []
        context_blocks: List[str] = []
        total_chars = 0
        used_chunks: List[Dict[str, Any]] = []

        # Deduplicate citations by document and page/section
        seen_citation_keys = set()

        for idx, chunk in enumerate(search_results, start=1):
            content = chunk.get("content", "").strip()
            if not content:
                continue

            # Check max chunks and character budget
            if len(context_blocks) >= self.max_chunks:
                break
            if total_chars + len(content) > self.max_context_chars:
                if len(context_blocks) >= 1:
                    break
                content = content[:max(100, self.max_context_chars - 300)] + "..."

            doc_name = chunk.get("document_name") or "Study Material"
            doc_id = chunk.get("document_id") or ""
            page = chunk.get("page_number")
            section = chunk.get("section_title")
            sim = chunk.get("similarity", 0.0)

            # Build header
            header_parts = [f"Source [{idx}]: {doc_name}"]
            if page:
                header_parts.append(f"Page {page}")
            if section:
                header_parts.append(f"Section: {section}")
            header_parts.append(f"(Relevance: {int(sim * 100)}%)")

            header_str = " | ".join(header_parts)
            block = f"--- {header_str} ---\n{content}\n"

            context_blocks.append(block)
            total_chars += len(block)
            used_chunks.append(chunk)

            # Record citation
            cite_key = f"{doc_id}_{page}_{section}"
            if cite_key not in seen_citation_keys:
                seen_citation_keys.add(cite_key)
                citations.append(
                    SourceCitation(
                        document_id=doc_id,
                        document_name=doc_name,
                        page_number=page,
                        section_title=section,
                        chunk_id=chunk.get("chunk_id"),
                        similarity_score=sim,
                    )
                )

        formatted_str = "\n".join(context_blocks)
        return RAGContext(
            formatted_context=formatted_str,
            citations=citations,
            retrieved_chunks=used_chunks,
            total_characters=total_chars,
            chunk_count=len(context_blocks),
        )
