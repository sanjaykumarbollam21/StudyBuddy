from typing import List, Dict, Any, Optional
import re


class PrelimsMCQEngine:
    """
    Phase K: Advanced Competitive Prelims Examination & MCQ Intelligence Engine.
    Supports statement-based, assertion-reason, match-following, chronology, and elimination tactics.
    Performs cognitive error diagnosis distinguishing knowledge gaps from careless reading and time pressure.
    """

    ERROR_TAXONOMY = {
        "KNOWLEDGE_ERROR": "Did not study or recall the core factual/conceptual rule.",
        "READING_ERROR": "Overlooked 'not', 'except', 'incorrect', or qualifying terms in question stem.",
        "CARELESS_ERROR": "Marked quickly without reading all options carefully.",
        "GUESSING_ERROR": "Low confidence speculative guess that backfired under negative marking.",
        "TIME_PRESSURE": "Rushed answer due to ticking session clock.",
        "MISCONCEPTION": "Conflated two superficially similar but legally distinct concepts.",
    }

    ELIMINATION_INDICATORS = [
        {"pattern": r"\b(always|never|completely|exclusively|solely|under all circumstances)\b", "heuristic": "Extreme qualifier — historically often false in competitive exam statements."},
        {"pattern": r"\b(can be|may include|generally|in some circumstances|potentially)\b", "heuristic": "Moderate inclusive qualifier — historically often true in dynamic science & ecology statements."},
    ]

    def evaluate_mcq_response(
        self,
        question_type: str,
        correct_answer: str,
        student_response: str,
        marks_per_question: float = 2.0,
        negative_ratio: float = 0.33,
        time_spent_seconds: int = 60,
        confidence_level: str = "medium",
        user_declared_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates student choice, computes net marks with negative penalty,
        and categorizes cognitive error.
        """
        is_correct = student_response.strip().upper() == correct_answer.strip().upper()
        penalty = round(marks_per_question * negative_ratio, 2)
        marks_awarded = marks_per_question if is_correct else -penalty

        error_category = None
        advice = None

        if not is_correct:
            if user_declared_error in self.ERROR_TAXONOMY:
                error_category = user_declared_error
            elif time_spent_seconds < 15:
                error_category = "CARELESS_ERROR"
            elif confidence_level == "high":
                error_category = "MISCONCEPTION"
            elif confidence_level == "low":
                error_category = "GUESSING_ERROR"
            elif time_spent_seconds > 100:
                error_category = "TIME_PRESSURE"
            else:
                error_category = "KNOWLEDGE_ERROR"

            advice = self.ERROR_TAXONOMY[error_category]

        return {
            "is_correct": is_correct,
            "marks_awarded": marks_awarded,
            "penalty_applied": penalty if not is_correct else 0.0,
            "error_category": error_category,
            "diagnostic_feedback": advice if not is_correct else "Well deduced! Accurate elimination and recall.",
            "time_spent_seconds": time_spent_seconds,
            "confidence_level": confidence_level,
        }

    def detect_elimination_tactics(self, statement_text: str) -> List[Dict[str, str]]:
        """
        Detects structural linguistic cues in competitive exam statements to teach
        effective objective elimination strategies.
        """
        detected = []
        for item in self.ELIMINATION_INDICATORS:
            if re.search(item["pattern"], statement_text, re.IGNORECASE):
                detected.append({
                    "qualifier_type": "extreme" if "always" in item["pattern"] else "inclusive",
                    "tactic_hint": item["heuristic"],
                })
        return detected

    def detect_extreme_qualifiers(self, statement_text: str) -> bool:
        """Checks if a statement contains extreme qualifiers like always, never, completely."""
        extreme_pattern = r"\b(always|never|completely|exclusively|solely|under all circumstances)\b"
        return bool(re.search(extreme_pattern, statement_text, re.IGNORECASE))

    def generate_practice_question(
        self,
        exam_id: str = "upsc_cse",
        subject: str = "Indian Polity",
        topic: str = "Fundamental Rights",
        question_type: str = "statement_based",
    ) -> Dict[str, Any]:
        """Generates a structured Prelims MCQ with elimination hints."""
        return {
            "id": "mcq-sim-01",
            "exam_id": exam_id,
            "subject": subject,
            "topic": topic,
            "question_type": question_type,
            "question_text": f"Consider the following statements regarding {topic} in the context of {subject}:\n1. It is enforceable in the court of law.\n2. It can be curtailed during times of emergency under specific constitutional provisions.",
            "options": [
                {"label": "A", "text": "1 only"},
                {"label": "B", "text": "2 only"},
                {"label": "C", "text": "Both 1 and 2"},
                {"label": "D", "text": "Neither 1 nor 2"},
            ],
            "correct_answer": "C",
            "marks": 2.0,
            "negative_marks": 0.66,
            "explanation": f"Both statements are constitutionally sound principles of {topic}.",
            "elimination_hints": self.detect_elimination_tactics("It is enforceable in the court of law."),
        }


PrelimsEngine = PrelimsMCQEngine
