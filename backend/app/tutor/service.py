import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document, DocumentChunk
from app.schemas.tutor import (
    TutorAskRequest,
    TutorAskResponse,
    DocumentSessionResponse,
    GroundingMode,
    SourceCitation,
)
from app.search.hybrid import KnowledgeSearchService
from app.search.context_builder import RAGContextBuilder
from app.tutor.grounding import (
    SYSTEM_PROMPTS,
    STRICT_MATERIALS_FALLBACK,
    build_tutor_prompt,
)
from app.tutor.providers import get_llm_provider, LLMProvider
from app.core.config import settings

class TutorService:
    """
    Orchestrates the RAG-grounded AI Teacher:
    Search -> Context Building -> Prompt Assembly -> LLM Generation -> Citations.
    """

    def __init__(
        self,
        session: AsyncSession,
        search_service: KnowledgeSearchService,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.session = session
        self.search_service = search_service
        self.context_builder = RAGContextBuilder()
        self.llm_provider = llm_provider or get_llm_provider()

    async def ask_tutor(
        self,
        user_id: str,
        request: TutorAskRequest,
    ) -> TutorAskResponse:
        grounding_mode = request.grounding_mode or GroundingMode.MATERIALS_PLUS_GENERAL

        context_text = ""
        citations: List[SourceCitation] = []
        context_used = False

        # In STRICT or MATERIALS_PLUS_GENERAL mode, perform hybrid retrieval from user knowledge base
        if grounding_mode != GroundingMode.GENERAL:
            from app.search.context_builder import MAX_RAG_CHUNKS
            search_results = await self.search_service.search_hybrid(
                user_id=user_id,
                query=request.query,
                top_k=MAX_RAG_CHUNKS,
                document_ids=request.document_ids,
                subject=request.subject,
                collection=request.collection,
            )

            threshold = settings.SIMILARITY_THRESHOLD if grounding_mode == GroundingMode.STRICT_MATERIALS else 0.25
            relevant_results = [r for r in search_results if r.get("similarity", 0.0) >= threshold]

            if relevant_results:
                rag_ctx = self.context_builder.build_context(relevant_results)
                context_text = rag_ctx.formatted_context
                citations = rag_ctx.citations
                context_used = len(citations) > 0
            else:
                context_used = False

        # Anti-hallucination guard: If strict materials mode has no relevant context, return fallback
        if grounding_mode == GroundingMode.STRICT_MATERIALS and not context_used:
            return TutorAskResponse(
                answer=STRICT_MATERIALS_FALLBACK,
                sources=[],
                grounding_mode=grounding_mode,
                context_used=False,
                session_id=request.session_id,
            )

        system_instruction = SYSTEM_PROMPTS.get(
            grounding_mode,
            SYSTEM_PROMPTS[GroundingMode.MATERIALS_PLUS_GENERAL]
        )
        prompt = build_tutor_prompt(
            student_query=request.query,
            context_text=context_text,
            grounding_mode=grounding_mode,
        )

        answer = await self.llm_provider.generate_response(
            prompt=prompt,
            system_prompt=system_instruction,
        )

        return TutorAskResponse(
            answer=answer,
            sources=citations,
            grounding_mode=grounding_mode,
            context_used=context_used,
            session_id=request.session_id,
        )

    async def start_document_session(
        self,
        document_id: str,
        user_id: str,
    ) -> DocumentSessionResponse:
        """
        Creates a scoped session when the student clicks 'Teach Me This' on a document.
        """
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await self.session.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Document not found or access denied")

        # Fetch section titles to suggest study topics
        chunk_stmt = select(DocumentChunk.section_title).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.user_id == user_id,
            DocumentChunk.section_title.isnot(None),
        ).distinct()
        section_titles = (await self.session.execute(chunk_stmt)).scalars().all()
        suggested = [t for t in section_titles if t and t.strip()][:4]

        if not suggested:
            suggested = ["Core Concepts Overview", "Key Definitions", "Exam Practice Questions"]

        session_id = f"tutor-doc-{uuid.uuid4()}"
        welcome_msg = (
            f"Hello! I'm ready to teach you directly from your material '{doc.filename}'. "
            f"All our questions, quizzes, and explanations will be grounded in this document."
        )

        return DocumentSessionResponse(
            document_id=doc.id,
            document_name=doc.filename,
            session_id=session_id,
            welcome_message=welcome_msg,
            suggested_topics=suggested,
        )
