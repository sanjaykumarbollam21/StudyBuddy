from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class ReadinessEngine:
    """
    Computes a multi-factor exam readiness score and qualitative diagnostic projection
    synthesizing Knowledge Coverage, Concept Mastery, Active Recall Retrievability,
    Practice Accuracy, Mock Exam Results, and Time-Management Efficiency.
    """

    def compute_exam_readiness(
        self,
        blueprint: Dict[str, float],
        topic_masteries: Dict[str, float],
        recall_stats: Optional[Dict[str, Any]] = None,
        practice_stats: Optional[Dict[str, Any]] = None,
        mock_stats: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates holistic readiness across 7 dimensions.
        """
        blueprint_topics = list(blueprint.keys())
        total_topics = len(blueprint_topics) if blueprint_topics else 1

        # 1. Knowledge Coverage (Percentage of blueprint topics student has interacted with)
        covered_topics = [t for t in blueprint_topics if topic_masteries.get(t, 0.0) > 10.0]
        coverage_pct = (len(covered_topics) / total_topics) * 100.0

        # 2. Weighted Concept Mastery across blueprint
        weighted_mastery_sum = 0.0
        total_weight = 0.0
        weak_topics: List[str] = []
        strong_topics: List[str] = []
        critical_topics: List[str] = []

        for topic, weight in blueprint.items():
            mastery = topic_masteries.get(topic, 45.0)  # default prior baseline
            weighted_mastery_sum += mastery * weight
            total_weight += weight

            if mastery >= 75.0:
                strong_topics.append(topic)
            elif mastery < 40.0:
                critical_topics.append(topic)
            elif mastery < 60.0:
                weak_topics.append(topic)

        concept_mastery_pct = (weighted_mastery_sum / total_weight) if total_weight > 0 else 50.0

        # 3. Recent Recall Retrievability (SM-2 health)
        # Defaults to 70% if student hasn't done spaced revision yet
        recall_pct = 70.0
        if recall_stats:
            total_items = recall_stats.get("total_items", 0)
            due_items = recall_stats.get("due_items", 0)
            if total_items > 0:
                # Retrievability is higher when fewer items are overdue
                recall_pct = max(20.0, 100.0 - ((due_items / total_items) * 50.0))

        # 4. Practice Accuracy
        practice_pct = 65.0
        if practice_stats:
            practice_pct = practice_stats.get("average_accuracy", 65.0)

        # 5. Mock Exam Performance
        mock_pct = 60.0
        if mock_stats:
            mock_pct = mock_stats.get("latest_score", 60.0)

        # 6. Time Management Efficiency
        time_efficiency_pct = 75.0
        if mock_stats:
            unanswered_ratio = mock_stats.get("unanswered_ratio", 0.0)
            time_efficiency_pct = max(30.0, 100.0 - (unanswered_ratio * 100.0))

        # 7. Weak Area Severity Penalty
        # Severe penalty if critical topics exist in heavily weighted areas
        weak_penalty = min(20.0, len(critical_topics) * 6.0 + len(weak_topics) * 2.5)

        # Multi-factor weighted aggregate
        raw_readiness = (
            (0.18 * coverage_pct) +
            (0.24 * concept_mastery_pct) +
            (0.14 * recall_pct) +
            (0.14 * practice_pct) +
            (0.18 * mock_pct) +
            (0.12 * time_efficiency_pct)
        ) - weak_penalty

        final_readiness = round(max(5.0, min(99.0, raw_readiness)), 1)

        # Category
        if final_readiness >= 80.0:
            category = "High Exam Readiness"
        elif final_readiness >= 60.0:
            category = "Moderate Exam Readiness"
        else:
            category = "At Risk / Requires Focus"

        # Construct actionable recommendation projection
        problem_topics = critical_topics + [t for t in weak_topics if t not in critical_topics]
        if problem_topics:
            top_focus = ", ".join(problem_topics[:2])
            sessions = min(4, max(2, len(problem_topics) + 1))
            actionable_projection = (
                f"At your current study rate, your weakest areas are likely to remain {top_focus}. "
                f"Spend your next {sessions} sessions there."
            )
        else:
            actionable_projection = (
                "You have balanced mastery across all blueprint topics. "
                "Focus on timed mock exams to optimize speed and eliminate minor slips."
            )

        readiness_message = f"You're approximately {int(final_readiness)}% ready for this exam."

        return {
            "readiness_percentage": final_readiness,
            "readiness_category": category,
            "readiness_message": readiness_message,
            "actionable_projection": actionable_projection,
            "dimension_scores": {
                "knowledge_coverage": round(coverage_pct, 1),
                "concept_mastery": round(concept_mastery_pct, 1),
                "recent_recall": round(recall_pct, 1),
                "practice_accuracy": round(practice_pct, 1),
                "mock_test_performance": round(mock_pct, 1),
                "time_management": round(time_efficiency_pct, 1),
                "weak_penalty_applied": round(weak_penalty, 1),
            },
            "strong_topics": strong_topics,
            "weak_topics": weak_topics,
            "critical_topics": critical_topics,
        }
