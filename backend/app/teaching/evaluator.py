from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.teaching.state import ConceptStep, EvaluationVerdict
from app.tutor.providers.base import LLMProvider

class EvaluationResult(BaseModel):
    verdict: EvaluationVerdict
    feedback: str
    misconception_identified: Optional[str] = None
    confidence: float = 1.0
    mastery_delta: float = 0.0
    needs_remediation: bool = False
    source: str = "model"
    ideas_present: List[str] = Field(default_factory=list)
    ideas_missing: List[str] = Field(default_factory=list)

class AnswerEvaluationService:
    """
    Evaluates student responses against concept expectations,
    identifying correctness, partial understanding, and misconceptions.
    Uses extraction-based LLM grading and derives verdicts deterministically in code.
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

        # Delegate extraction to LLMProvider
        eval_dict = await self.llm_provider.evaluate_student_answer(
            concept_title=step.title,
            question=step.check_question,
            expected_concept=step.expected_core_concept,
            student_answer=student_answer,
            common_misconceptions=step.common_misconceptions,
            context_text=context_text,
            key_ideas=step.key_ideas,
        )

        ideas_present = list(eval_dict.get("ideas_present", []))
        ideas_missing = list(eval_dict.get("ideas_missing", []))
        misconception = eval_dict.get("misconception_identified")
        is_unsure = bool(eval_dict.get("is_off_topic_or_unsure", False))
        feedback = str(eval_dict.get("feedback", ""))
        confidence = float(eval_dict.get("confidence", 0.9))
        source = str(eval_dict.get("source", "model"))

        ans_lower = student_answer.lower().strip()
        is_explicit_dont_know = any(
            p in ans_lower for p in ["don't know", "dont know", "no idea", "not sure", "explain this to me", "please explain"]
        )

        # DETERMINISTIC VERDICT DERIVATION IN CODE:
        # - all ideas present -> correct
        # - some ideas present -> partially_correct
        # - a stated wrong belief -> misconception
        # - nothing relevant or an explicit "don't know" -> struggling
        if is_explicit_dont_know or is_unsure:
            verdict = EvaluationVerdict.STRUGGLING
            mastery_delta = 0.0
            needs_remediation = True
        elif misconception:
            verdict = EvaluationVerdict.MISCONCEPTION
            mastery_delta = 0.0
            needs_remediation = True
        elif "ideas_present" in eval_dict or "ideas_missing" in eval_dict:
            # Extraction-based evaluation
            if len(ideas_present) > 0 and len(ideas_missing) == 0:
                verdict = EvaluationVerdict.CORRECT
                mastery_delta = 25.0
                needs_remediation = False
            elif len(ideas_present) > 0:
                verdict = EvaluationVerdict.PARTIALLY_CORRECT
                mastery_delta = 10.0
                needs_remediation = False
            else:
                verdict = EvaluationVerdict.STRUGGLING
                mastery_delta = 0.0
                needs_remediation = True
        elif "verdict" in eval_dict:
            # Backward compatibility with mock or direct verdict providers
            v_raw = str(eval_dict["verdict"]).lower()
            if v_raw == "correct":
                verdict = EvaluationVerdict.CORRECT
                mastery_delta = 25.0
                needs_remediation = False
            elif v_raw == "misconception":
                verdict = EvaluationVerdict.MISCONCEPTION
                mastery_delta = 0.0
                needs_remediation = True
            elif v_raw == "struggling":
                verdict = EvaluationVerdict.STRUGGLING
                mastery_delta = 0.0
                needs_remediation = True
            else:
                verdict = EvaluationVerdict.PARTIALLY_CORRECT
                mastery_delta = 10.0
                needs_remediation = False
        else:
            verdict = EvaluationVerdict.STRUGGLING
            mastery_delta = 0.0
            needs_remediation = True

        return EvaluationResult(
            verdict=verdict,
            feedback=feedback or "Let's review this concept together.",
            misconception_identified=misconception,
            confidence=confidence,
            mastery_delta=mastery_delta,
            needs_remediation=needs_remediation,
            source=source,
            ideas_present=ideas_present,
            ideas_missing=ideas_missing,
        )
