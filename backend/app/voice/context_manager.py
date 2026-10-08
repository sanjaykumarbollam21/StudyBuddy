import re
from enum import Enum
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.learning import StudentMastery


class VoiceIntent(str, Enum):
    EXPLAIN_TOPIC = "explain_topic"
    QUIZ_ME = "quiz_me"
    HINT = "hint"
    SIMPLIFY = "simplify"
    NEXT_QUESTION = "next_question"
    PAGE_EXPLANATION = "page_explanation"
    IMAGE_EXPLANATION = "image_explanation"
    ANSWER = "answer"


class ConversationContextManager:
    """
    Maintains conversational pedagogical memory across voice and multimodal dialogue turns.
    Tracks subject, topic, concept step, known misconceptions, active learning goals,
    and classifies student spoken voice intents.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    def classify_voice_intent(self, text: str, has_image: bool = False) -> Dict[str, Any]:
        """
        Classifies student utterance into pedagogical voice commands.
        """
        cleaned = text.lower().strip()

        # Check for page references e.g. "explain page 42"
        page_match = re.search(r'(?:explain|teach|read|what(?:\'s| is) on)?\s*page\s*(\d+)', cleaned)
        if page_match:
            page_num = int(page_match.group(1))
            return {
                "intent": VoiceIntent.PAGE_EXPLANATION,
                "page_number": page_num,
                "extracted_target": f"Page {page_num}",
            }

        # Check for image inquiries
        if has_image and any(k in cleaned for k in ["diagram", "image", "chart", "picture", "this show", "this mean", "explain this"]):
            return {
                "intent": VoiceIntent.IMAGE_EXPLANATION,
                "extracted_target": "Current Image/Diagram",
            }

        # Check for hints
        if any(k in cleaned for k in ["hint", "give me a clue", "help me with this", "clue"]):
            return {
                "intent": VoiceIntent.HINT,
                "extracted_target": "Hint Request",
            }

        # Check for simplification / analogies
        if any(k in cleaned for k in ["make it easier", "simpler", "explain simpler", "simple analogy", "too hard", "don't understand", "dont understand", "confused"]):
            return {
                "intent": VoiceIntent.SIMPLIFY,
                "extracted_target": "Simplification / Analogy",
            }

        # Check for quiz request
        if any(k in cleaned for k in ["quiz me", "test me", "test my knowledge", "ask me a question", "give me a question"]):
            return {
                "intent": VoiceIntent.QUIZ_ME,
                "extracted_target": "Knowledge Check Probe",
            }

        # Check for next question / advance
        if any(k in cleaned for k in ["ask me another", "next question", "next concept", "what's next", "whats next", "move on", "continue"]):
            return {
                "intent": VoiceIntent.NEXT_QUESTION,
                "extracted_target": "Next Concept",
            }

        # Check for topic switch: "explain deadlocks to me"
        topic_match = re.search(r'(?:explain|teach me|tell me about|how does|what is|what are)\s+([a-zA-Z\s]+?)(?:\s+to me|\s+please)?$', cleaned)
        if topic_match:
            candidate = topic_match.group(1).strip()
            if len(candidate) > 3 and candidate not in ["it", "this", "that", "more"]:
                return {
                    "intent": VoiceIntent.EXPLAIN_TOPIC,
                    "extracted_target": candidate.title(),
                }

        # Default: normal student answer or conceptual reflection
        return {
            "intent": VoiceIntent.ANSWER,
            "extracted_target": None,
        }

    async def get_student_pedagogical_context(
        self,
        user_id: str,
        topic: str,
    ) -> Dict[str, Any]:
        """
        Retrieves real mastery and active misconceptions from StudentMastery database.
        """
        mastery_score = 50.0
        weak_areas: List[str] = []

        if self.db:
            try:
                res = await self.db.execute(
                    select(StudentMastery).where(
                        StudentMastery.user_id == user_id,
                        StudentMastery.topic_id.ilike(f"%{topic}%"),
                    )
                )
                sm = res.scalars().first()
                if sm:
                    mastery_score = sm.mastery_percentage
                    weak_areas = sm.weak_areas or []
            except Exception:
                pass

        return {
            "topic": topic,
            "mastery_score": mastery_score,
            "weak_areas": weak_areas,
            "is_struggling": mastery_score < 60.0 or len(weak_areas) > 0,
        }
