import re
from typing import Dict, Any, Optional
from app.tutor.providers.base import LLMProvider
from app.tutor.grounding import STRICT_MATERIALS_FALLBACK

class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for tests, continuous integration, and offline local development.
    Faithfully simulates grounded AI Teacher responses according to grounding policies
    and the Phase 4A Socratic pedagogical contract.
    """

    def get_provider_name(self) -> str:
        return "mock"

    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        is_strict = "STRICT_MATERIALS" in system_prompt
        has_context = "STUDENT'S PERSONAL KNOWLEDGE BASE CONTEXT" in prompt

        if is_strict and not has_context:
            return STRICT_MATERIALS_FALLBACK

        # Extract student question
        q_match = re.search(r"Student Question:\s*(.*?)(?:\n\n|\Z)", prompt, re.DOTALL)
        question = q_match.group(1).strip() if q_match else "your question"

        # Extract source title mentions if available in prompt
        doc_mentions = re.findall(r"Source \[\d+\]: ([^|\n]+)", prompt)
        primary_doc = doc_mentions[0].strip() if doc_mentions else "your notes"

        if is_strict:
            return (
                f"Based directly on your study material '{primary_doc}':\n\n"
                f"Regarding '{question}', the document details that this concept functions "
                f"through the structured rules and principles outlined in your syllabus.\n\n"
                f"Key takeaway from your material: All properties and algorithms follow the "
                f"exact definitions recorded in your uploaded chapter."
            )

        if "MATERIALS_PLUS_GENERAL" in system_prompt:
            if has_context:
                return (
                    f"### From your study materials ({primary_doc}):\n"
                    f"Your notes define '{question}' in detail. Specifically, the material emphasizes "
                    f"the core mechanisms, steps, and theoretical foundations covered in your course.\n\n"
                    f"### Additional explanation & intuition:\n"
                    f"Think of this concept like an everyday orchestration: just as tasks in an office "
                    f"require scheduled turns and shared resources, this system ensures orderly progression "
                    f"without bottlenecks or conflicts."
                )
            else:
                return (
                    f"### General Explanation:\n"
                    f"Here is a clear step-by-step breakdown of '{question}':\n\n"
                    f"1. Core Definition: It is a fundamental mechanism designed to organize and process operations.\n"
                    f"2. Practical Analogy: Imagine an organized queue ensuring fairness and preventing starvation.\n\n"
                    f"Tip: Upload your course notes or lecture slides to enable Study Buddy to teach using your professor's exact syllabus!"
                )

        # General mode
        return (
            f"Here is a step-by-step lesson on '{question}':\n\n"
            f"First, let's understand the problem this solves. In computing systems, managing resources "
            f"efficiently is vital for optimal performance.\n\n"
            f"Does this make sense so far, or would you like an analogy?"
        )

    async def evaluate_student_answer(
        self,
        concept_title: str,
        question: str,
        expected_concept: str,
        student_answer: str,
        common_misconceptions: Optional[Dict[str, str]] = None,
        context_text: str = "",
    ) -> Dict[str, Any]:
        ans = student_answer.lower()

        if any(term in ans for term in ["don't know", "hint", "help", "not sure", "confused"]):
            return {
                "verdict": "struggling",
                "feedback": "No problem! Let's approach it from a simpler angle.",
                "misconception_identified": None,
                "confidence": 1.0,
            }

        if any(term in ans for term in ["cpu", "slow", "hardware", "speed"]):
            return {
                "verdict": "misconception",
                "feedback": "You're thinking about performance, which is a reasonable connection, but that's not the cause of deadlock.",
                "misconception_identified": "CPU too slow",
                "confidence": 0.95,
            }

        if any(term in ans for term in ["waiting", "other has", "blocked", "circular", "neither", "held", "holds", "other"]):
            return {
                "verdict": "correct",
                "feedback": "Exactly. You identified the key idea: circular waiting.",
                "misconception_identified": None,
                "confidence": 0.98,
            }

        return {
            "verdict": "partially_correct",
            "feedback": "You're touching on part of the problem. Remember to focus on resource ownership.",
            "misconception_identified": None,
            "confidence": 0.70,
        }

    async def generate_remediation(
        self,
        concept_title: str,
        student_answer: str,
        misconception: Optional[str],
        original_analogy: str,
        context_text: str = "",
    ) -> Dict[str, Any]:
        return {
            "re_explanation": (
                "Let's simplify it. Imagine two people each holding one key..."
            ),
            "simpler_analogy": (
                "Imagine two people: Person A has Key 1 and needs Key 2, while Person B has Key 2 and needs Key 1."
            ),
            "simpler_question": (
                "If Person A has Key 1 and needs Key 2, while Person B has Key 2 and needs Key 1, what happens?"
            ),
            "hint": "Neither person can open their door without the other person's key.",
        }
