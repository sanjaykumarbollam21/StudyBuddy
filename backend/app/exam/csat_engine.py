from typing import List, Dict, Any, Optional
import uuid


class CSATEngine:
    """
    Phase L: Civil Services Aptitude Test (CSAT Paper II) Engine.
    Qualifying paper assessment covering Reading Comprehension, Logical Reasoning,
    and Basic Numeracy with targeted timed practice sessions.
    """

    CURATED_CSAT_QUESTIONS = [
        {
            "id": "csat-rc-01",
            "category": "reading_comprehension",
            "passage": (
                "The expansion of renewable energy capacity requires not only capital deployment "
                "but also modernization of transmission grids and long-duration storage systems. "
                "Intermittent generation without storage creates grid instability, necessitating "
                "continued reliance on thermal baseload."
            ),
            "question_text": "Which of the following is the most logical and crucial corollary that can be drawn from the passage?",
            "options": [
                {"label": "A", "text": "Renewable energy cannot completely replace thermal energy under any circumstances."},
                {"label": "B", "text": "Investment in transmission and storage must accompany green energy capacity expansion."},
                {"label": "C", "text": "Grid modernization is more important than building solar installations."},
                {"label": "D", "text": "Thermal baseload plants should receive higher subsidies than solar projects."},
            ],
            "correct_answer": "B",
            "explanation": "The passage argues that without transmission grids and storage systems, intermittent renewable power causes instability, requiring grid modernization alongside capacity addition.",
            "difficulty": "medium",
        },
        {
            "id": "csat-num-02",
            "category": "basic_numeracy",
            "question_text": (
                "A student scores 25% in an examination and fails by 30 marks. "
                "Another student who gets 50% marks gets 20 marks more than the minimum passing marks. "
                "What is the maximum pass mark percentage required?"
            ),
            "options": [
                {"label": "A", "text": "33%"},
                {"label": "B", "text": "40%"},
                {"label": "C", "text": "45%"},
                {"label": "D", "text": "35%"},
            ],
            "correct_answer": "B",
            "explanation": "Difference in percentage = 50% - 25% = 25%. Difference in marks = 30 + 20 = 50 marks. 25% = 50 marks, so Total = 200 marks. Student 1 scored 25% of 200 = 50 marks. Pass mark = 50 + 30 = 80 marks. Pass percentage = (80 / 200) * 100 = 40%.",
            "difficulty": "medium",
        },
        {
            "id": "csat-lr-03",
            "category": "logical_reasoning",
            "question_text": (
                "Statements:\n1. Some officers are teachers.\n2. All teachers are researchers.\n"
                "Conclusions:\nI. Some researchers are officers.\nII. Some teachers are not researchers.\n"
                "Which conclusion logically follows?"
            ),
            "options": [
                {"label": "A", "text": "Only Conclusion I follows"},
                {"label": "B", "text": "Only Conclusion II follows"},
                {"label": "C", "text": "Both I and II follow"},
                {"label": "D", "text": "Neither I nor II follows"},
            ],
            "correct_answer": "A",
            "explanation": "Since some officers are teachers, and all teachers are researchers, the intersection between officers and researchers is non-empty. Conclusion I follows. Since all teachers are researchers, Conclusion II is false.",
            "difficulty": "easy",
        },
    ]

    def create_csat_session(
        self,
        duration_minutes: int = 30,
        focus_category: Optional[str] = None,
        question_count: int = 10,
    ) -> Dict[str, Any]:
        """
        Synthesizes a targeted 30-minute CSAT sprint.
        Distributes comprehension, reasoning, and numeracy according to student focus.
        """
        questions = list(self.CURATED_CSAT_QUESTIONS)
        if focus_category:
            questions = [q for q in questions if q["category"] == focus_category] or questions

        # Repeat to meet question_count if needed
        session_questions = []
        for i in range(question_count):
            base_q = dict(questions[i % len(questions)])
            base_q["session_question_id"] = f"csat-sq-{i+1}"
            session_questions.append(base_q)

        return {
            "session_id": f"csat-{uuid.uuid4().hex[:10]}",
            "title": f"{duration_minutes}-Minute CSAT Focused Sprint",
            "duration_minutes": duration_minutes,
            "total_questions": len(session_questions),
            "qualifying_threshold_marks": 66.0,  # 33% out of 200
            "marks_per_question": 2.5,
            "negative_penalty": 0.83,
            "questions": session_questions,
            "instructions": "Speed and accuracy are essential. Maintain a steady pace of ~2 minutes per comprehension passage.",
        }

    @classmethod
    def generate_practice_session(
        cls,
        difficulty: str = "medium",
        count: int = 10,
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Classmethod bridge for practice session generation."""
        engine = cls()
        session = engine.create_csat_session(
            duration_minutes=max(15, count * 2),
            focus_category=topic,
            question_count=count,
        )
        session["negative_marking_penalty"] = session["negative_penalty"]
        session["time_limit_minutes"] = session["duration_minutes"]
        return session
