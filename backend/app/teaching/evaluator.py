from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.teaching.state import ConceptStep, EvaluationVerdict
from app.tutor.providers.base import LLMProvider

class EvaluationResult(BaseModel):
    verdict: EvaluationVerdict
    feedback: str
    misconception_identified: Optional[str] = None
    confidence: float = 1.0
    mastery_delta: float = 0.0
    needs_remediation: bool = False

class AnswerEvaluationService:
    """
    Evaluates student responses against concept expectations,
    identifying correctness, partial understanding, and misconceptions.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def evaluate_answer(
        self,
        step: ConceptStep,
        student_answer: str,
        context_text: str = "",
        action_type: str = "answer",
    ) -> EvaluationResult:
        """
        Evaluates student answer for the active concept step.
        """
        if action_type == "request_hint":
            return EvaluationResult(
                verdict=EvaluationVerdict.HINT_REQUESTED,
                feedback=f"Here is a hint: {step.socratic_hint or 'Think about what each process needs versus what it possesses.'}",
                needs_remediation=True,
                mastery_delta=0.0,
            )

        if action_type == "request_simpler":
            return EvaluationResult(
                verdict=EvaluationVerdict.STRUGGLING,
                feedback="Let's simplify this concept so it's intuitive and tangible.",
                needs_remediation=True,
                mastery_delta=0.0,
            )

        # Delegate evaluation to LLMProvider (local Socratic, mock, or cloud)
        eval_dict = await self.llm_provider.evaluate_student_answer(
            concept_title=step.title,
            question=step.check_question,
            expected_concept=step.expected_core_concept,
            student_answer=student_answer,
            common_misconceptions=step.common_misconceptions,
            context_text=context_text,
        )

        verdict_str = eval_dict.get("verdict", "partially_correct").lower()
        feedback = eval_dict.get("feedback", "")
        misconception = eval_dict.get("misconception_identified")
        confidence = float(eval_dict.get("confidence", 0.8))

        if verdict_str == "correct":
            return EvaluationResult(
                verdict=EvaluationVerdict.CORRECT,
                feedback=feedback or "Exactly. You identified the key idea.",
                mastery_delta=25.0,
                needs_remediation=False,
                confidence=confidence,
            )
        elif verdict_str == "misconception":
            return EvaluationResult(
                verdict=EvaluationVerdict.MISCONCEPTION,
                feedback=feedback or "That is a common misconception.",
                misconception_identified=misconception,
                mastery_delta=0.0,
                needs_remediation=True,
                confidence=confidence,
            )
        elif verdict_str == "struggling":
            return EvaluationResult(
                verdict=EvaluationVerdict.STRUGGLING,
                feedback=feedback or "Let's break this down into a simpler example.",
                mastery_delta=0.0,
                needs_remediation=True,
                confidence=confidence,
            )
        else:
            return EvaluationResult(
                verdict=EvaluationVerdict.PARTIALLY_CORRECT,
                feedback=feedback or "You're getting close, but there's a vital nuance to notice.",
                mastery_delta=10.0,
                needs_remediation=False,
                confidence=confidence,
            )
