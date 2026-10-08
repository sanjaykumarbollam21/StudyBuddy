from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class LLMProvider(ABC):
    """
    First-class abstract interface for LLM completion and pedagogical teaching.
    Ensures that both offline local models and cloud providers adhere to
    the exact same Socratic teaching contract and grounding constraints.
    """

    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        """Standard prompt completion."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    @abstractmethod
    async def evaluate_student_answer(
        self,
        concept_title: str,
        question: str,
        expected_concept: str,
        student_answer: str,
        common_misconceptions: Optional[Dict[str, str]] = None,
        context_text: str = "",
    ) -> Dict[str, Any]:
        """
        Diagnostically evaluate student response.
        Returns:
            {
                "verdict": "correct" | "partially_correct" | "misconception" | "struggling",
                "feedback": str,
                "misconception_identified": str | None,
                "confidence": float
            }
        """
        pass

    @abstractmethod
    async def generate_remediation(
        self,
        concept_title: str,
        student_answer: str,
        misconception: Optional[str],
        original_analogy: str,
        context_text: str = "",
    ) -> Dict[str, Any]:
        """
        Generate simpler remediation when student struggles.
        Returns:
            {
                "re_explanation": str,
                "simpler_analogy": str,
                "simpler_question": str,
                "hint": str
            }
        """
        pass

    async def stream_response(self, prompt: str, system_prompt: str):
        """Asynchronously stream response tokens."""
        text = await self.generate_response(prompt, system_prompt)
        words = text.split(" ")
        for i, word in enumerate(words):
            yield (word + (" " if i < len(words) - 1 else ""))
