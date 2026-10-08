from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.teaching.state import ConceptStep
from app.tutor.providers.base import LLMProvider

class RemediationPackage(BaseModel):
    re_explanation: str
    simpler_analogy: str
    simpler_question: str
    hint: str

class AdaptiveRemediationService:
    """
    Formulates pedagogical remediation when a student has a misconception
    or struggles with a concept.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def create_remediation(
        self,
        step: ConceptStep,
        student_answer: str,
        misconception: Optional[str] = None,
        context_text: str = "",
    ) -> RemediationPackage:
        """
        Builds adaptive re-explanation with simpler analogies and guided questions.
        """
        # First check if the step already has tailored simpler analogy
        if step.simpler_analogy and step.common_misconceptions and misconception:
            re_expl = step.common_misconceptions.get(
                misconception,
                "Let's look at this from a simpler, more direct angle."
            )
            simpler_q = f"Let's test this simpler case: {step.simpler_analogy}\nWhat happens in this scenario?"
            return RemediationPackage(
                re_explanation=re_expl,
                simpler_analogy=step.simpler_analogy,
                simpler_question=simpler_q,
                hint=step.socratic_hint or "Focus on who has what and who needs what.",
            )

        # Otherwise delegate to LLM provider
        data = await self.llm_provider.generate_remediation(
            concept_title=step.title,
            student_answer=student_answer,
            misconception=misconception,
            original_analogy=step.analogy,
            context_text=context_text,
        )

        return RemediationPackage(
            re_explanation=data.get("re_explanation", "Let's simplify this concept."),
            simpler_analogy=data.get("simpler_analogy", step.simpler_analogy or step.analogy),
            simpler_question=data.get("simpler_question", step.check_question),
            hint=data.get("hint", step.socratic_hint or "Think about the simplest physical example."),
        )
