"""
Concept Extractor for Study Buddy.
Extracts concepts, topics, sub-concepts, and prerequisite relationships
from uploaded document chunks and section titles to construct a KnowledgeGraph.
Works 100% deterministically/offline with optional LLM enhancement.
"""

import re
from typing import List, Dict, Any, Optional, Set
from app.curriculum.graph import KnowledgeGraph, ConceptNode
from app.models.document import DocumentChunk
from app.tutor.providers import LLMProvider


class DocumentConceptExtractor:
    """
    Extracts concepts and prerequisite DAG edges from uploaded document chunks.
    """

    PREREQUISITE_MARKERS = [
        r"prerequisite[s]?:?\s*([^.\n]+)",
        r"requires?(?:\s+prior)?(?:\s+knowledge\s+of)?\s*([^.\n]+)",
        r"before(?:\s+studying|\s+proceeding\s+to|\s+learning)?\s*([^,.\n]+)",
        r"builds\s+upon\s*([^.\n]+)",
        r"assumes\s+(?:familiarity|knowledge)\s+with\s*([^.\n]+)",
        r"foundation(?:al)?(?:\s+for)?\s*([^.\n]+)",
    ]

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider

    def extract_from_chunks(
        self,
        chunks: List[DocumentChunk],
        document_title: str = "Uploaded Document",
        subject: str = "Uploaded Material",
    ) -> KnowledgeGraph:
        """
        Builds a KnowledgeGraph DAG from sorted document chunks.
        """
        kg = KnowledgeGraph(name=f"Curriculum from {document_title}")
        if not chunks:
            # Fallback if document is empty
            node = ConceptNode(
                id=f"doc-{hash(document_title) % 100000}",
                title=document_title,
                description=f"Overview and foundations of {document_title}.",
                subject=subject,
                difficulty="beginner",
                estimated_mins=30,
                learning_objectives=[f"Master core concepts from {document_title}"],
            )
            kg.add_node(node)
            return kg

        # Step 1: Group chunks by section title or synthesize distinct concept clusters
        sections: Dict[str, List[DocumentChunk]] = {}
        for chunk in sorted(chunks, key=lambda c: (c.page_number or 1, c.chunk_index)):
            sec_name = (chunk.section_title or "").strip()
            if not sec_name:
                sec_name = f"Section {chunk.chunk_index + 1}"
            if sec_name not in sections:
                sections[sec_name] = []
            sections[sec_name].append(chunk)

        # If too few sections, segment into meaningful concept milestones
        if len(sections) < 2 and len(chunks) > 1:
            sections = {}
            for i, chunk in enumerate(chunks):
                first_line = chunk.content.split("\n")[0][:60].strip()
                title = first_line if len(first_line) > 5 else f"Part {i+1}: {document_title}"
                sections[title] = [chunk]

        # Step 2: Create ConceptNode for each section
        extracted_nodes: List[ConceptNode] = []
        for i, (sec_title, sec_chunks) in enumerate(sections.items()):
            combined_text = " ".join([c.content for c in sec_chunks])
            node_id = f"node-{i+1}"

            # Extract sub-concepts (bullet points, bold text, capitalized terms)
            sub_concepts = self._extract_sub_concepts(combined_text)
            description = self._extract_summary(combined_text)
            difficulty = self._infer_difficulty(i, len(sections), combined_text)
            mins = max(20, min(60, len(combined_text.split()) // 30))

            node = ConceptNode(
                id=node_id,
                title=sec_title,
                description=description,
                subject=subject,
                difficulty=difficulty,
                estimated_mins=mins,
                sub_concepts=sub_concepts[:4],
                learning_objectives=[
                    f"Explain key principles of {sec_title}.",
                    f"Apply {sec_title} concepts to solve domain problems.",
                ],
            )
            extracted_nodes.append(node)
            kg.add_node(node)

        # Step 3: Infer prerequisite relations
        # Heuristic 1: Sequential chapter flow (earlier sections are natural prerequisites for immediate successors)
        for i in range(len(extracted_nodes) - 1):
            curr_node = extracted_nodes[i]
            next_node = extracted_nodes[i + 1]
            kg.add_prerequisite(curr_node.id, next_node.id)

        # Heuristic 2: Explicit linguistic dependency markers
        for i, node in enumerate(extracted_nodes):
            sec_text = " ".join([c.content for c in sections.get(node.title, [])])
            for pattern in self.PREREQUISITE_MARKERS:
                matches = re.findall(pattern, sec_text, re.IGNORECASE)
                for match in matches:
                    matched_target = match.lower().strip()
                    # Check if matched text references an earlier node
                    for other_node in extracted_nodes[:i]:
                        if other_node.title.lower() in matched_target or matched_target in other_node.title.lower():
                            kg.add_prerequisite(other_node.id, node.id)

        # Step 4: Validate DAG and break any accidental cycles
        if kg.has_cycle():
            # In case an edge introduced a cycle, revert to pure chronological DAG
            clean_kg = KnowledgeGraph(name=kg.name)
            for node in extracted_nodes:
                node.prerequisites = []
                clean_kg.add_node(node)
            for i in range(len(extracted_nodes) - 1):
                clean_kg.add_prerequisite(extracted_nodes[i].id, extracted_nodes[i + 1].id)
            return clean_kg

        return kg

    def _extract_sub_concepts(self, text: str) -> List[str]:
        """Finds key phrases, markdown headers, and highlighted terms."""
        sub = []
        # Look for markdown bullets or bold phrases
        bold_matches = re.findall(r"\*\*([^*]+)\*\*", text)
        for b in bold_matches:
            b_clean = b.strip()
            if 3 < len(b_clean) < 40 and b_clean not in sub:
                sub.append(b_clean)

        # Look for bullet points
        bullet_matches = re.findall(r"(?:^|\n)[*\-•]\s+([^:\n]+)", text)
        for bm in bullet_matches:
            bm_clean = bm.strip()
            if 3 < len(bm_clean) < 40 and bm_clean not in sub:
                sub.append(bm_clean)

        return sub

    def _extract_summary(self, text: str) -> str:
        """Extracts first 1-2 meaningful sentences for description."""
        sentences = [s.strip() for s in re.split(r"[.\n]+", text) if len(s.strip()) > 15]
        if sentences:
            return ". ".join(sentences[:2]) + "."
        return "Core concepts and principles."

    def _infer_difficulty(self, index: int, total: int, text: str) -> str:
        if index == 0 or total <= 2:
            return "beginner"
        if index >= total - 1 and total > 3:
            return "advanced"
        return "intermediate"

    def generate_learning_pack_from_document(
        self,
        chunks: List[DocumentChunk],
        document_title: str = "Uploaded Document",
        subject: str = "Uploaded Material",
    ) -> Dict[str, Any]:
        """
        Creates an end-to-end Learning Pack from document chunks:
        1. KnowledgeGraph (concepts, prerequisites DAG)
        2. Structured Chapters (order, summaries, key takeaways)
        3. Grounded Lesson Plans (Socratic prompts, objectives)
        4. Grounded Practice Questions (distractors, explanations)
        """
        kg = self.extract_from_chunks(chunks, document_title=document_title, subject=subject)

        # Build chapters from graph nodes
        chapters = []
        for i, node in enumerate(kg.nodes.values()):
            chapters.append({
                "chapter_index": i + 1,
                "concept_id": node.id,
                "title": node.title,
                "summary": node.description,
                "difficulty": node.difficulty,
                "estimated_mins": node.estimated_mins,
                "sub_concepts": node.sub_concepts,
                "learning_objectives": node.learning_objectives,
                "prerequisites": node.prerequisites,
            })

        # Build grounded lessons
        lessons = []
        for chap in chapters:
            lessons.append({
                "lesson_id": f"lesson-{chap['concept_id']}",
                "title": f"Mastering {chap['title']}",
                "concept_id": chap["concept_id"],
                "socratic_prompt": f"Let's explore {chap['title']}. What is your current understanding of how this works?",
                "key_takeaways": chap["sub_concepts"] if chap["sub_concepts"] else [chap["summary"]],
                "estimated_mins": chap["estimated_mins"],
            })

        # Grounded questions using QuestionGenerator
        from app.practice.generator import QuestionGenerator
        q_gen = QuestionGenerator(llm_provider=self.llm_provider)
        practice_questions = []
        for chap in chapters:
            chap_chunks = [c for c in chunks if (c.section_title or "").strip() == chap["title"]]
            if not chap_chunks and chunks:
                chap_chunks = chunks[:2]
            q_list = q_gen.generate_questions(
                topic=chap["title"],
                count=2,
                rag_chunks=chap_chunks,
            )
            for q in q_list:
                practice_questions.append({
                    "id": q.id,
                    "concept_id": chap["concept_id"],
                    "concept_tag": chap["title"],
                    "question_type": q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
                    "prompt": q.prompt,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
                })

        return {
            "document_title": document_title,
            "subject": subject,
            "knowledge_graph": {
                "nodes": [n.to_dict() for n in kg.nodes.values()],
                "edges": [{"from": u, "to": v} for u, targets in kg.adj.items() for v in targets],
            },
            "chapters": chapters,
            "lessons": lessons,
            "practice_questions": practice_questions,
            "total_chapters": len(chapters),
            "total_questions": len(practice_questions),
        }
