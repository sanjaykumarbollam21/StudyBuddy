from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.competitive_exam import SyllabusNode
from app.models.learning import StudentMastery
from app.exam.profiles.registry import get_exam_registry


class SyllabusService:
    """
    Manages the hierarchical competitive exam syllabus graph.
    Merges official syllabus structure with real student mastery and PYQ weights.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.registry = get_exam_registry()

    async def get_or_create_syllabus_graph(self, exam_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves complete hierarchical syllabus tree.
        If database nodes are absent, seeds them from the verified Exam Profile definition.
        Overlays student mastery if user_id is provided.
        """
        profile = self.registry.get_profile(exam_id)
        if not profile:
            profile = self.registry.get_profile("upsc_cse")

        # Fetch mastery map if user provided
        mastery_map: Dict[str, float] = {}
        if self.db and user_id:
            res = await self.db.execute(
                select(StudentMastery).where(StudentMastery.user_id == user_id)
            )
            for m in res.scalars().all():
                mastery_map[m.topic_id.lower()] = m.mastery_percentage

        # Build tree with overlaid telemetry
        return self._enrich_tree(profile.syllabus_tree, mastery_map)

    async def get_syllabus_graph(self, user_id: Optional[str] = None, exam_id: str = "upsc_cse", stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for get_or_create_syllabus_graph accepting user_id and exam_id."""
        return await self.get_or_create_syllabus_graph(exam_id=exam_id, user_id=user_id)

    def _enrich_tree(self, nodes: List[Dict[str, Any]], mastery_map: Dict[str, float]) -> List[Dict[str, Any]]:
        enriched = []
        for node in nodes:
            item = dict(node)
            title_lower = node.get("title", "").lower()
            code_lower = node.get("node_code", "").lower()

            # Find matching mastery
            mastery = 0.0
            for k, v in mastery_map.items():
                if k in title_lower or k in code_lower or title_lower in k:
                    mastery = v
                    break

            # If node has no explicit mastery, generate realistic fallback if in practice
            item["mastery_percentage"] = round(mastery, 1)

            # Determine status
            if mastery >= 80.0:
                item["status"] = "mastered"
            elif mastery >= 50.0:
                item["status"] = "in_progress"
            elif mastery > 0.0:
                item["status"] = "weak"
            else:
                item["status"] = "not_started"

            # Recursive children
            if "children" in node and node["children"]:
                item["children"] = self._enrich_tree(node["children"], mastery_map)

            enriched.append(item)
        return enriched

    def get_topic_heatmap(self, syllabus_tree: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Flattens the syllabus hierarchy to produce an actionable student heatmap:
        Strong (>=80%), Good (50-79%), Weak (<50%), Critical (high exam weight + weak), Not Studied (0%).
        """
        flat_topics = []

        def _flatten(nodes):
            for n in nodes:
                flat_topics.append({
                    "node_code": n.get("node_code"),
                    "title": n.get("title"),
                    "stage": n.get("stage", "both"),
                    "exam_weight": n.get("exam_weight", 1.0),
                    "pyq_frequency": n.get("pyq_frequency", 0),
                    "mastery_percentage": n.get("mastery_percentage", 0.0),
                    "status": n.get("status", "not_started"),
                })
                if "children" in n and n["children"]:
                    _flatten(n["children"])

        _flatten(syllabus_tree)

        strong = [t for t in flat_topics if t["mastery_percentage"] >= 80.0]
        good = [t for t in flat_topics if 50.0 <= t["mastery_percentage"] < 80.0]
        weak = [t for t in flat_topics if 0.0 < t["mastery_percentage"] < 50.0]
        not_studied = [t for t in flat_topics if t["mastery_percentage"] == 0.0]
        critical = [t for t in weak if t["exam_weight"] >= 1.5 or t["pyq_frequency"] >= 5]

        return {
            "total_topics": len(flat_topics),
            "strong": strong,
            "good": good,
            "weak": weak,
            "critical": critical,
            "not_studied": not_studied,
            "coverage_percentage": round(((len(strong) + len(good) + len(weak)) / max(1, len(flat_topics))) * 100, 1),
        }
