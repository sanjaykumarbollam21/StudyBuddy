"""
Curriculum & Roadmap Service for Study Buddy.
Coordinates KnowledgeGraph, StudentMastery, RAG documents, and roadmap generation.
Enforces the architectural separation:
  - Knowledge Graph = What exists and how concepts relate (DAG)
  - Mastery Model = What the student understands
  - Curriculum Engine = What the student should learn next
"""

import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.curriculum.graph import KnowledgeGraph, ConceptNode, get_curated_knowledge_graph
from app.curriculum.extractor import DocumentConceptExtractor
from app.models.learning import LearningPath, LearningPathTopic, StudentMastery, Topic
from app.models.document import Document, DocumentChunk


def utc_now():
    return datetime.now(timezone.utc)


class CurriculumService:
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.extractor = DocumentConceptExtractor()

    async def generate_roadmap(
        self,
        user_id: str,
        subject: str,
        goal: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates or updates a personalized roadmap for a subject or document.
        """
        # Step 1: Obtain or build the KnowledgeGraph
        kg: Optional[KnowledgeGraph] = None
        source_type = "foundational"

        if document_id and self.db:
            doc_res = await self.db.execute(select(Document).where(Document.id == document_id))
            doc = doc_res.scalars().first()
            if doc:
                source_type = "user_materials"
                chunks_res = await self.db.execute(
                    select(DocumentChunk).where(DocumentChunk.document_id == document_id)
                )
                chunks = chunks_res.scalars().all()
                kg = self.extractor.extract_from_chunks(
                    chunks=chunks,
                    document_title=doc.title or subject,
                    subject=subject,
                )

        if not kg:
            kg = get_curated_knowledge_graph(subject)

        # Fallback dynamic graph if no pre-built curriculum found
        if not kg:
            kg = self._build_dynamic_graph(subject)
            source_type = "hybrid"

        # Step 2: Fetch user's existing mastery
        mastered_topics: Set[str] = set()
        mastery_map: Dict[str, float] = {}

        if self.db:
            mastery_res = await self.db.execute(
                select(StudentMastery).where(StudentMastery.user_id == user_id)
            )
            for m in mastery_res.scalars().all():
                mastery_map[m.topic_id.lower()] = m.mastery_percentage
                if m.mastery_percentage >= 80.0:
                    mastered_topics.add(m.topic_id.lower())

        # Step 3: Topologically sort nodes to guarantee prerequisite ordering
        ordered_nodes = kg.topological_sort()

        # Step 4: Determine initial node states (locked, unlocked, in_progress, mastered)
        roadmap_topics_data = []
        completed_count = 0
        frontier_selected = False

        for index, node in enumerate(ordered_nodes):
            norm_title = node.title.lower()
            norm_id = node.id.lower()

            # Check mastery
            score = mastery_map.get(norm_id, mastery_map.get(norm_title, 0.0))
            is_mastered = score >= 80.0 or norm_title in mastered_topics or norm_id in mastered_topics

            # Check if all prerequisites are mastered
            prereq_nodes = kg.get_prerequisites(node.id)
            prereqs_satisfied = True
            for p in prereq_nodes:
                p_norm_id = p.id.lower()
                p_norm_title = p.title.lower()
                if p_norm_id not in mastered_topics and p_norm_title not in mastered_topics:
                    prereqs_satisfied = False
                    break

            if is_mastered:
                status = "mastered"
                completed_count += 1
            elif prereqs_satisfied:
                if not frontier_selected:
                    status = "in_progress"
                    frontier_selected = True
                else:
                    status = "unlocked"
            else:
                status = "locked"

            roadmap_topics_data.append({
                "order_index": index + 1,
                "custom_title": node.title,
                "description": node.description,
                "difficulty": node.difficulty,
                "estimated_minutes": node.estimated_mins,
                "status": status,
                "mastery_score": score,
                "prerequisites": [p.title for p in prereq_nodes],
                "sub_concepts": node.sub_concepts,
                "learning_objectives": node.learning_objectives,
            })

        # If nothing was selected as in_progress (e.g. none started or all mastered)
        if not frontier_selected:
            for item in roadmap_topics_data:
                if item["status"] == "unlocked":
                    item["status"] = "in_progress"
                    break

        roadmap_id = f"lp-{uuid.uuid4().hex[:12]}"
        title = f"{subject} Mastery Track"
        if not goal:
            goal = f"Master fundamental and advanced concepts in {subject}"

        # Step 5: Persist to DB if database session is provided
        if self.db:
            learning_path = LearningPath(
                id=roadmap_id,
                user_id=user_id,
                title=title,
                goal=goal,
                source_type=source_type,
                total_steps=len(roadmap_topics_data),
                completed_steps=completed_count,
                status="completed" if completed_count == len(roadmap_topics_data) and completed_count > 0 else "in_progress",
            )
            self.db.add(learning_path)
            await self.db.flush()

            for item in roadmap_topics_data:
                lpt = LearningPathTopic(
                    id=f"lpt-{uuid.uuid4().hex[:12]}",
                    learning_path_id=roadmap_id,
                    order_index=item["order_index"],
                    custom_title=item["custom_title"],
                    description=item["description"],
                    difficulty=item["difficulty"],
                    estimated_minutes=item["estimated_minutes"],
                    status=item["status"],
                    prerequisites=item["prerequisites"],
                    learning_objectives=item["learning_objectives"],
                )
                self.db.add(lpt)

            await self.db.commit()

        return {
            "id": roadmap_id,
            "title": title,
            "subject": subject,
            "goal": goal,
            "source_type": source_type,
            "total_steps": len(roadmap_topics_data),
            "completed_steps": completed_count,
            "progress_percentage": round((completed_count / len(roadmap_topics_data) * 100), 1) if roadmap_topics_data else 0.0,
            "status": "in_progress",
            "topics": roadmap_topics_data,
        }

    async def get_roadmap(self, user_id: str, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a roadmap and dynamically reflects latest student mastery.
        """
        if not self.db:
            return None

        res = await self.db.execute(
            select(LearningPath).where(LearningPath.id == roadmap_id, LearningPath.user_id == user_id)
        )
        path = res.scalars().first()
        if not path:
            return None

        topics_res = await self.db.execute(
            select(LearningPathTopic)
            .where(LearningPathTopic.learning_path_id == roadmap_id)
            .order_by(LearningPathTopic.order_index)
        )
        topics = topics_res.scalars().all()

        # Fetch latest mastery
        mastery_res = await self.db.execute(
            select(StudentMastery).where(StudentMastery.user_id == user_id)
        )
        mastery_map = {m.topic_id.lower(): m.mastery_percentage for m in mastery_res.scalars().all()}

        # Build set of mastered titles
        mastered_titles = set()
        for t in topics:
            score = mastery_map.get(t.custom_title.lower(), 0.0)
            if score >= 80.0 or t.status == "mastered":
                mastered_titles.add(t.custom_title.lower())

        topic_dicts = []
        completed_count = 0
        frontier_assigned = False

        for t in topics:
            score = mastery_map.get(t.custom_title.lower(), 0.0)
            prereqs = t.prerequisites or []
            all_prereqs_met = all(p.lower() in mastered_titles for p in prereqs)

            if score >= 80.0 or t.status == "mastered":
                status = "mastered"
                completed_count += 1
            elif all_prereqs_met:
                if not frontier_assigned:
                    status = "in_progress"
                    frontier_assigned = True
                else:
                    status = "unlocked"
            else:
                status = "locked"

            topic_dicts.append({
                "id": t.id,
                "order_index": t.order_index,
                "custom_title": t.custom_title,
                "description": t.description,
                "difficulty": t.difficulty,
                "estimated_minutes": t.estimated_minutes,
                "status": status,
                "mastery_score": score,
                "prerequisites": prereqs,
                "learning_objectives": t.learning_objectives or [],
            })

        return {
            "id": path.id,
            "title": path.title,
            "goal": path.goal,
            "source_type": path.source_type,
            "total_steps": len(topic_dicts),
            "completed_steps": completed_count,
            "progress_percentage": round((completed_count / len(topic_dicts) * 100), 1) if topic_dicts else 0.0,
            "status": "completed" if completed_count == len(topic_dicts) and completed_count > 0 else path.status,
            "topics": topic_dicts,
        }

    async def get_next_recommendation(
        self,
        user_id: str,
        roadmap_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Answers: 'What should I learn next?'
        Finds the highest-priority unlocked, unmastered frontier concept.
        """
        # If roadmap_id is given, pull from that roadmap; otherwise pull latest active
        roadmap = None
        if roadmap_id:
            roadmap = await self.get_roadmap(user_id, roadmap_id)
        elif self.db:
            latest_res = await self.db.execute(
                select(LearningPath)
                .where(LearningPath.user_id == user_id)
                .order_by(LearningPath.created_at.desc())
            )
            latest = latest_res.scalars().first()
            if latest:
                roadmap = await self.get_roadmap(user_id, latest.id)

        # If still no roadmap exists, auto-generate default Operating Systems roadmap
        if not roadmap:
            roadmap = await self.generate_roadmap(user_id, "Operating Systems")

        topics = roadmap.get("topics", [])

        # Find frontier: in_progress or first unlocked topic
        next_topic = None
        for t in topics:
            if t["status"] == "in_progress":
                next_topic = t
                break
        if not next_topic:
            for t in topics:
                if t["status"] == "unlocked":
                    next_topic = t
                    break

        if not next_topic and topics:
            # If all are mastered or locked, return the last topic or first
            next_topic = topics[0]

        # Formulate pedagogical recommendation reason
        prereqs = next_topic.get("prerequisites", [])
        if prereqs:
            why_text = (
                f"You are ready for '{next_topic['custom_title']}' because you have satisfied its "
                f"core prerequisites: {', '.join(prereqs)}. Mastering this now will build crucial "
                f"domain intuition."
            )
        else:
            why_text = (
                f"'{next_topic['custom_title']}' is the foundational starting point for {roadmap['title']}. "
                f"No prior prerequisites are required."
            )

        return {
            "roadmap_id": roadmap["id"],
            "roadmap_title": roadmap["title"],
            "topic_title": next_topic["custom_title"],
            "description": next_topic.get("description", ""),
            "difficulty": next_topic.get("difficulty", "medium"),
            "estimated_minutes": next_topic.get("estimated_minutes", 30),
            "status": next_topic["status"],
            "prerequisites": prereqs,
            "learning_objectives": next_topic.get("learning_objectives", []),
            "why_recommended": why_text,
        }

    async def explain_why_learning(
        self,
        user_id: str,
        topic_title: str,
        roadmap_id: Optional[str] = None,
        goal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Answers: 'Why am I learning this?'
        Connects prior prerequisites, current importance, future unlocks, and student goal.
        """
        # Search roadmap or curated knowledge graphs
        kg = get_curated_knowledge_graph(topic_title)
        node = kg.get_node(topic_title) if kg else None

        prereqs = [p.title for p in kg.get_prerequisites(node.id)] if (kg and node) else []
        dependents = [d.title for d in kg.get_dependents(node.id)] if (kg and node) else []

        # Generate structured 4-part pedagogical rationale
        prereq_rationale = (
            f"It directly builds upon concepts you've reviewed in {', '.join(prereqs)}."
            if prereqs else "It provides the bedrock foundational model with no prerequisites needed."
        )

        future_rationale = (
            f"Mastering this unlocks advanced topics including: {', '.join(dependents)}."
            if dependents else "This is a capstone concept integrating all preceding principles."
        )

        core_value = (
            node.description if node else f"Understanding {topic_title} is crucial for real-world mastery."
        )

        goal_alignment = (
            f"Directly advances your goal: '{goal}'." if goal
            else f"Equips you with deep conceptual mastery in {topic_title}."
        )

        full_explanation = (
            f"**Why Learn {topic_title}?**\n\n"
            f"1. **Conceptual Foundation:** {prereq_rationale}\n\n"
            f"2. **Core Domain Value:** {core_value}\n\n"
            f"3. **What It Unlocks:** {future_rationale}\n\n"
            f"4. **Goal Alignment:** {goal_alignment}"
        )

        return {
            "topic_title": topic_title,
            "prerequisites": prereqs,
            "unlocked_next": dependents,
            "full_explanation": full_explanation,
            "core_value": core_value,
            "prerequisite_connection": prereq_rationale,
            "future_unlocks": future_rationale,
        }

    async def update_progress_from_mastery(
        self,
        user_id: str,
        topic_title: str,
        mastery_score: float,
    ) -> None:
        """
        Updates student mastery and unlocks subsequent roadmap topics if >= 80%.
        """
        if not self.db:
            return

        norm_title = topic_title.lower().strip()

        # Update or create StudentMastery
        mastery_res = await self.db.execute(
            select(StudentMastery).where(
                StudentMastery.user_id == user_id,
                StudentMastery.topic_id == topic_title,
            )
        )
        record = mastery_res.scalars().first()
        if not record:
            record = StudentMastery(
                id=f"sm-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                topic_id=topic_title,
                mastery_percentage=mastery_score,
                times_practiced=1,
                last_evaluated_at=utc_now(),
            )
            self.db.add(record)
        else:
            record.mastery_percentage = max(record.mastery_percentage, mastery_score)
            record.times_practiced += 1
            record.last_evaluated_at = utc_now()

        # Update any LearningPathTopic matching this topic
        if mastery_score >= 80.0:
            topics_res = await self.db.execute(
                select(LearningPathTopic).where(
                    LearningPathTopic.custom_title.ilike(f"%{topic_title}%")
                )
            )
            for lpt in topics_res.scalars().all():
                lpt.status = "mastered"

        await self.db.commit()

    def _build_dynamic_graph(self, topic: str) -> KnowledgeGraph:
        """
        Constructs a structured 4-stage pedagogical DAG for custom subjects.
        """
        kg = KnowledgeGraph(name=f"{topic} Graph")
        nodes = [
            ConceptNode(
                id=f"{topic.lower()}-1",
                title=f"{topic} Fundamentals & Core Principles",
                description=f"Essential terminology, core mental models, and foundational building blocks of {topic}.",
                subject=topic,
                difficulty="beginner",
                estimated_mins=30,
                learning_objectives=[f"Define core terminology of {topic}.", "Identify foundational components."],
            ),
            ConceptNode(
                id=f"{topic.lower()}-2",
                title=f"{topic} Architecture & Mechanics",
                description=f"How {topic} mechanisms work under the hood and interact with other systems.",
                subject=topic,
                difficulty="intermediate",
                estimated_mins=45,
                prerequisites=[f"{topic} Fundamentals & Core Principles"],
                learning_objectives=[f"Describe operational mechanics of {topic}."],
            ),
            ConceptNode(
                id=f"{topic.lower()}-3",
                title=f"Applied {topic} & Practical Patterns",
                description=f"Solving concrete problems, avoiding common pitfalls, and real-world usage of {topic}.",
                subject=topic,
                difficulty="intermediate",
                estimated_mins=45,
                prerequisites=[f"{topic} Architecture & Mechanics"],
                learning_objectives=[f"Apply {topic} to real-world scenarios."],
            ),
            ConceptNode(
                id=f"{topic.lower()}-4",
                title=f"Advanced {topic} & System Optimization",
                description=f"Performance optimization, edge cases, and architectural best practices in {topic}.",
                subject=topic,
                difficulty="advanced",
                estimated_mins=60,
                prerequisites=[f"Applied {topic} & Practical Patterns"],
                learning_objectives=[f"Analyze tradeoffs and optimize {topic} systems."],
            ),
        ]
        for n in nodes:
            kg.add_node(n)

        for i in range(len(nodes) - 1):
            kg.add_prerequisite(nodes[i].id, nodes[i + 1].id)

        return kg

    async def generate_learning_pack(
        self,
        user_id: str,
        document_id: str,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive learning pack (chapters, lessons, questions, DAG)
        grounded in the uploaded document.
        """
        doc = None
        chunks = []
        if self.db:
            doc_res = await self.db.execute(select(Document).where(Document.id == document_id))
            doc = doc_res.scalars().first()
            chunks_res = await self.db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            chunks = list(chunks_res.scalars().all())

        title = doc.title if doc and doc.title else "Uploaded Document"
        subj = subject or (doc.subject_name if doc and doc.subject_name else "Uploaded Material")
        return self.extractor.generate_learning_pack_from_document(
            chunks=chunks,
            document_title=title,
            subject=subj,
        )
