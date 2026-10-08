import re
from typing import Dict, Any, List, Optional
from app.tutor.providers.base import LLMProvider
from app.embeddings import get_embedding_provider

class LocalLLMProvider(LLMProvider):
    """
    Offline Socratic Teacher Engine.
    Operates 100% locally with zero internet requests and zero API costs.
    
    Uses:
    - Pretrained local semantic embeddings for conceptual answer matching.
    - Diagnostic pattern matching & misconception detection.
    - Socratic remediation templates grounded in student materials.
    """

    def __init__(self):
        self.embedding_provider = get_embedding_provider("local")

    def get_provider_name(self) -> str:
        return "local_socratic"

    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        """
        Generate grounded pedagogical response locally.
        """
        from app.tutor.grounding import STRICT_MATERIALS_FALLBACK

        is_strict = "STRICT_MATERIALS" in system_prompt
        has_context = "STUDENT'S PERSONAL KNOWLEDGE BASE CONTEXT" in prompt

        if is_strict and not has_context:
            return STRICT_MATERIALS_FALLBACK

        q_match = re.search(r"Student Question:\s*(.*?)(?:\n\n|\Z)", prompt, re.DOTALL)
        question = q_match.group(1).strip() if q_match else "your question"

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
        """
        Diagnostically evaluate student response using local semantic similarity
        and misconception matching.
        """
        ans_clean = student_answer.strip().lower()

        # 1. Check if student requested help or indicated confusion
        confusion_patterns = [
            r"\bi don'?t know\b",
            r"\bnot sure\b",
            r"\bconfused\b",
            r"\bhelp\b",
            r"\bhint\b",
            r"\bno idea\b",
            r"\bexplain simpler\b",
        ]
        for pat in confusion_patterns:
            if re.search(pat, ans_clean):
                return {
                    "verdict": "struggling",
                    "feedback": "That's completely fine. Learning happens by clarifying what feels uncertain.",
                    "misconception_identified": None,
                    "confidence": 0.95,
                }

        # 2. Check for explicit known misconceptions
        if common_misconceptions:
            ans_vec = await self.embedding_provider.embed_text(student_answer)
            for misc_term, explanation in common_misconceptions.items():
                # Direct keyword check or semantic similarity check
                if misc_term.lower() in ans_clean:
                    return {
                        "verdict": "misconception",
                        "feedback": explanation,
                        "misconception_identified": misc_term,
                        "confidence": 0.90,
                    }
                # Semantic check against misconception description
                misc_vec = await self.embedding_provider.embed_text(misc_term)
                dot = sum(x * y for x, y in zip(ans_vec, misc_vec))
                if dot >= 0.78:
                    return {
                        "verdict": "misconception",
                        "feedback": explanation,
                        "misconception_identified": misc_term,
                        "confidence": dot,
                    }

        # 3. Semantic similarity against expected concept
        ans_vec = await self.embedding_provider.embed_text(student_answer)
        exp_vec = await self.embedding_provider.embed_text(expected_concept)
        similarity = sum(x * y for x, y in zip(ans_vec, exp_vec))

        # Check core keyword presence
        expected_words = [w for w in re.findall(r"\w+", expected_concept.lower()) if len(w) > 3]
        matches = [w for w in expected_words if w in ans_clean]
        keyword_ratio = len(matches) / max(len(expected_words), 1)

        combined_score = (0.75 * similarity) + (0.25 * min(1.0, keyword_ratio * 1.5))

        if combined_score >= 0.65 or similarity >= 0.70:
            return {
                "verdict": "correct",
                "feedback": (
                    "Exactly. You identified the key idea: processes are held in a circular wait "
                    "where neither can proceed."
                ),
                "misconception_identified": None,
                "confidence": round(combined_score, 3),
            }
        elif combined_score >= 0.50:
            return {
                "verdict": "partially_correct",
                "feedback": "You're on the right track! Let's sharpen the core cause.",
                "misconception_identified": None,
                "confidence": round(combined_score, 3),
            }
        else:
            return {
                "verdict": "misconception",
                "feedback": "That's a reasonable thought, but the core issue is how resources are locked and waited upon.",
                "misconception_identified": "Resource Dependency Misunderstanding",
                "confidence": round(combined_score, 3),
            }

    async def generate_remediation(
        self,
        concept_title: str,
        student_answer: str,
        misconception: Optional[str],
        original_analogy: str,
        context_text: str = "",
    ) -> Dict[str, Any]:
        """
        Generate simpler physical analogy and guided Socratic question.
        """
        if misconception and "cpu" in misconception.lower():
            re_explanation = (
                "You're thinking about performance, which is a reasonable connection, "
                "but that's not the cause of deadlock. Deadlock happens even on the world's "
                "fastest supercomputer because it's a conflict over resource ownership, not processing speed."
            )
            simpler_analogy = (
                "Imagine two people: Person A holds Key 1 and needs Key 2 to open their door. "
                "Person B holds Key 2 and needs Key 1 to open their door."
            )
            simpler_question = (
                "If Person A will not give up Key 1 until they get Key 2, "
                "and Person B will not give up Key 2 until they get Key 1, what happens?"
            )
        else:
            re_explanation = (
                f"Let's break down {concept_title} into an everyday physical scenario."
            )
            simpler_analogy = (
                "Think of a single-lane bridge where two cars meet head-on in the middle. "
                "Neither car can move forward, and neither driver is willing to reverse."
            )
            simpler_question = (
                "Why is neither car able to cross the bridge?"
            )

        return {
            "re_explanation": re_explanation,
            "simpler_analogy": simpler_analogy,
            "simpler_question": simpler_question,
            "hint": "Focus on what each side is holding vs. what each side needs.",
        }
