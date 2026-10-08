import json
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

from app.tutor.providers.base import LLMProvider
from app.tutor.providers.local import LocalLLMProvider

logger = logging.getLogger(__name__)


class OllamaLLMProvider(LLMProvider):
    """
    Phase 13: Local LLM Provider for Ollama and llama.cpp-compatible daemons.
    Enables completely offline frontier inference on user machines.
    
    Includes:
    - Configurable model (default: llama3.2:3b, phi3:mini, mistral:7b).
    - Resource constraints optimized for 16 GB RAM PC (num_ctx: 2048, keep_alive: '5m').
    - Transparent fallback to LocalLLMProvider if Ollama daemon is offline.
    """

    def __init__(
        self,
        endpoint_url: str = "http://localhost:11434",
        model_name: str = "llama3.2:3b",
        fallback_on_error: bool = True,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_name = model_name
        self.fallback_on_error = fallback_on_error
        self._local_fallback = LocalLLMProvider()

    def get_provider_name(self) -> str:
        return f"ollama_{self.model_name}"

    def _call_ollama(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Send HTTP request to Ollama daemon."""
        url = f"{self.endpoint_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "temperature": 0.3,
            },
            "keep_alive": "5m",
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("response", "").strip()
        except Exception as e:
            logger.info(f"Ollama daemon unreachable at {self.endpoint_url} ({e}). Using local Socratic engine.")
            return None

    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        res = self._call_ollama(prompt, system_prompt)
        if res:
            return res
        if self.fallback_on_error:
            return await self._local_fallback.generate_response(prompt, system_prompt)
        raise RuntimeError(f"Ollama server at {self.endpoint_url} unreachable.")

    async def evaluate_student_answer(
        self,
        concept_title: str,
        question: str,
        expected_concept: str,
        student_answer: str,
        common_misconceptions: Optional[Dict[str, str]] = None,
        context_text: str = "",
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a strict Socratic Teacher evaluating a student response. "
            "Output JSON with keys: verdict ('correct', 'partially_correct', 'misconception', or 'struggling'), "
            "feedback (string), misconception_identified (string or null), confidence (float between 0.0 and 1.0)."
        )
        prompt = (
            f"Concept: {concept_title}\n"
            f"Question: {question}\n"
            f"Expected Concept: {expected_concept}\n"
            f"Student Answer: {student_answer}\n"
            f"Context: {context_text or 'N/A'}\n\n"
            f"Evaluate the student answer."
        )

        res = self._call_ollama(prompt, system_prompt)
        if res:
            try:
                clean = res.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                parsed = json.loads(clean)
                return {
                    "verdict": parsed.get("verdict", "partially_correct"),
                    "feedback": str(parsed.get("feedback", "Good effort.")),
                    "misconception_identified": parsed.get("misconception_identified"),
                    "confidence": float(parsed.get("confidence", 0.85)),
                }
            except Exception:
                pass

        return await self._local_fallback.evaluate_student_answer(
            concept_title=concept_title,
            question=question,
            expected_concept=expected_concept,
            student_answer=student_answer,
            common_misconceptions=common_misconceptions,
            context_text=context_text,
        )

    async def generate_remediation(
        self,
        concept_title: str,
        student_answer: str,
        misconception: Optional[str],
        original_analogy: str,
        context_text: str = "",
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a Socratic tutor generating remediation for a struggling student. "
            "Output JSON with keys: re_explanation, simpler_analogy, simpler_question, hint."
        )
        prompt = (
            f"Concept: {concept_title}\n"
            f"Student Answer: {student_answer}\n"
            f"Identified Misconception: {misconception or 'None'}\n"
            f"Original Analogy: {original_analogy}\n"
            f"Context: {context_text or 'N/A'}\n\n"
            f"Create a simplified physical analogy and guidance."
        )

        res = self._call_ollama(prompt, system_prompt)
        if res:
            try:
                clean = res.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                parsed = json.loads(clean)
                return {
                    "re_explanation": str(parsed.get("re_explanation", f"Let's revisit {concept_title}.")),
                    "simpler_analogy": str(parsed.get("simpler_analogy", original_analogy)),
                    "simpler_question": str(parsed.get("simpler_question", "What happens next?")),
                    "hint": str(parsed.get("hint", "Consider the dependencies.")),
                }
            except Exception:
                pass

        return await self._local_fallback.generate_remediation(
            concept_title=concept_title,
            student_answer=student_answer,
            misconception=misconception,
            original_analogy=original_analogy,
            context_text=context_text,
        )
