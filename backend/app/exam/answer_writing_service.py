from typing import List, Dict, Any, Optional
import re
from sqlalchemy.ext.asyncio import AsyncSession


class MainsAnswerWritingService:
    """
    Phase I & J: Competitive Exam Answer Writing & Pedagogical Evaluation Engine.
    Evaluates descriptive answers (UPSC GS I-IV, State PSC Mains, Essay, Banking Descriptive)
    using multidimensional pedagogical rubrics, identifying structural gaps, and generating outlines.
    """

    DEFAULT_RUBRIC_WEIGHTS = {
        "content_accuracy": 0.25,
        "structural_flow": 0.15,
        "syllabus_relevance": 0.15,
        "critical_analysis": 0.15,
        "examples_and_data": 0.10,
        "balanced_viewpoint": 0.10,
        "conclusion_forward_looking": 0.05,
        "presentation_and_subheadings": 0.05,
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    def evaluate_answer(
        self,
        question_text: str,
        student_answer: str,
        total_marks: float = 10.0,
        word_limit: int = 150,
        paper_name: str = "General Studies Paper II",
    ) -> Dict[str, Any]:
        """
        Deep pedagogical rubric evaluation of student's descriptive answer.
        Does NOT simply rewrite the answer; diagnoses strengths, missing dimensions, and concrete steps to improve.
        """
        words = student_answer.strip().split()
        word_count = len(words)
        text_lower = student_answer.lower()

        # 1. Dimension Checks & Heuristics
        has_intro = word_count >= 20 and any(k in text_lower[:150] for k in ["defined as", "refers to", "article", "established", "historically", "recently", "mandates"])
        has_subheadings = bool(re.search(r"(\n[A-Z0-9\.\-\: ]{3,35}\n)|(\*\*.*?\*\*)", student_answer))
        has_examples = any(k in text_lower for k in ["for example", "e.g.", "case law", "judgment", "committee", "report", "data", "survey", "such as"])
        has_articles = any(k in text_lower for k in ["article", "section", "act", "amendment", "schedule", "constitution"])
        has_critical_analysis = any(k in text_lower for k in ["however", "on the other hand", "challenges", "limitations", "counter", "bottlenecks", "concerns"])
        has_conclusion = any(k in text_lower[-250:] for k in ["way forward", "in conclusion", "therefore", "thus", "need of the hour", "future", "harmonious"])

        # 2. Score individual rubrics (0 - 100)
        content_score = 75.0 if has_articles or ("article" in question_text.lower() and has_intro) else 55.0
        if word_count < (word_limit * 0.4):
            content_score = max(20.0, content_score - 35.0)

        structure_score = 80.0 if (has_intro and (has_subheadings or len(student_answer.split('\n\n')) >= 3) and has_conclusion) else 50.0
        relevance_score = 75.0 if word_count >= (word_limit * 0.6) else 45.0
        analysis_score = 80.0 if has_critical_analysis else 45.0
        examples_score = 85.0 if has_examples else 40.0
        balance_score = 75.0 if has_critical_analysis else 50.0
        conclusion_score = 85.0 if has_conclusion else 35.0
        presentation_score = 80.0 if has_subheadings else 55.0

        rubric_scores = {
            "content_accuracy": content_score,
            "structural_flow": structure_score,
            "syllabus_relevance": relevance_score,
            "critical_analysis": analysis_score,
            "examples_and_data": examples_score,
            "balanced_viewpoint": balance_score,
            "conclusion_forward_looking": conclusion_score,
            "presentation_and_subheadings": presentation_score,
        }

        # 3. Composite score calculation
        composite_pct = sum(rubric_scores[k] * self.DEFAULT_RUBRIC_WEIGHTS[k] for k in self.DEFAULT_RUBRIC_WEIGHTS)
        marks_obtained = round((composite_pct / 100.0) * total_marks, 2)

        # 4. Strengths & Missing Dimensions Detection
        strengths = []
        if has_intro:
            strengths.append("Clear foundational introduction defining the key context.")
        if has_articles:
            strengths.append("Direct citation of constitutional provisions/statutory frameworks.")
        if has_critical_analysis:
            strengths.append("Balanced examination of operational challenges and bottlenecks.")
        if has_conclusion:
            strengths.append("Constructive, forward-looking concluding orientation.")
        if not strengths:
            strengths.append("Direct attempt addressing the question prompt.")

        missing_dimensions = []
        if not has_subheadings:
            missing_dimensions.append("Structured subheadings: Grouping points under clear thematic headings improves readability.")
        if not has_examples:
            missing_dimensions.append("Substantiating evidence: Add relevant committee reports (e.g. Sarkaria, Punchhi, Law Commission) or recent case laws.")
        if not has_critical_analysis:
            missing_dimensions.append("Multidimensional counter-perspective: Highlight administrative, economic, or legal counterarguments.")
        if not has_conclusion:
            missing_dimensions.append("Actionable 'Way Forward': Conclude with pragmatic policy recommendations or constitutional values.")
        if word_count < (word_limit * 0.7):
            missing_dimensions.append(f"Depth & length: Your answer contains {word_count} words; aim closer to the {word_limit} word requirement.")

        # 5. Model Answer Architecture Outline
        model_outline = (
            "### Recommended Answer Architecture:\n"
            "1. **Introduction (25-30 words)**: State the constitutional origin/statutory definition and historical genesis.\n"
            "2. **Body — Core Arguments (80-90 words)**:\n"
            "   - Dimension A (Legal/Institutional): Specific powers, duties, and mechanisms.\n"
            "   - Dimension B (Socio-Economic Impact): Grassroots realities, delivery challenges, and citizen rights.\n"
            "3. **Body — Challenges / Contemporary Gaps (30 words)**: Cite 2 specific operational bottlenecks with factual illustrations.\n"
            "4. **Way Forward & Conclusion (25-30 words)**: Reference committee recommendations or SDG/constitutional mandates to anchor a positive resolution."
        )

        improvement_guidelines = (
            f"Your answer scored {marks_obtained}/{total_marks} ({round(composite_pct)}%). "
            "To reach the top quartile (6.5+/10), prioritize subheadings, ground arguments in 2 authentic case examples, "
            "and always conclude with a distinct 'Way Forward' block."
        )

        return {
            "word_count": word_count,
            "word_limit": word_limit,
            "total_marks": total_marks,
            "marks_obtained": marks_obtained,
            "score_percentage": round(composite_pct, 1),
            "rubric_breakdown": rubric_scores,
            "strengths": strengths,
            "missing_dimensions": missing_dimensions,
            "improvement_guidelines": improvement_guidelines,
            "model_outline": model_outline,
            "paper_name": paper_name,
        }


AnswerWritingService = MainsAnswerWritingService
