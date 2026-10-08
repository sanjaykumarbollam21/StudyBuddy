import json
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

from app.tutor.providers.base import LLMProvider
from app.tutor.providers.local import LocalLLMProvider

logger = logging.getLogger(__name__)


class LlamaCppLLMProvider(LLMProvider):
    """
    Phase 14: Native llama.cpp HTTP daemon LLM Provider.
    Communicates with llama-server or llama.cpp daemon (typically running on port 8080).
    Supports both native llama.cpp `/completion` protocol and OpenAI-compatible `/v1/chat/completions`.
    
    Includes:
    - 16GB RAM constraints (n_predict: 512, temperature: 0.3, stop tokens).
    - Dual endpoint detection (/completion and /v1/chat/completions).
    - Transparent fallback to LocalLLMProvider if llama.cpp server is offline.
    """

    def __init__(
        self,
        endpoint_url: str = "http://localhost:8080",
        model_name: str = "llama.cpp-local",
        fallback_on_error: bool = True,
        use_chat_format: bool = False,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_name = model_name
        self.fallback_on_error = fallback_on_error
        self.use_chat_format = use_chat_format
        self._local_fallback = LocalLLMProvider()

    def get_provider_name(self) -> str:
        return f"llama_cpp_{self.model_name}"

    def _call_llama_cpp(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Send HTTP completion request to llama.cpp server."""
        if self.use_chat_format:
            url = f"{self.endpoint_url}/v1/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 512,
            }
        else:
            url = f"{self.endpoint_url}/completion"
            full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:"
            payload = {
                "prompt": full_prompt,
                "n_predict": 512,
                "temperature": 0.3,
                "stop": ["\nUser:", "<|endoftext|>", "</s>"],
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
                    if self.use_chat_format:
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
                    else:
                        return data.get("content", "").strip()
        except Exception as e:
            logger.info(f"llama.cpp daemon unreachable at {self.endpoint_url} ({e}). Falling back to local Socratic engine.")
            return None

        return None

    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        res = self._call_llama_cpp(prompt, system_prompt)
        if res:
            return res
        if self.fallback_on_error:
            return await self._local_fallback.generate_response(prompt, system_prompt)
        raise RuntimeError(f"llama.cpp server at {self.endpoint_url} unreachable.")

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

        res = self._call_llama_cpp(prompt, system_prompt)
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

        res = self._call_llama_cpp(prompt, system_prompt)
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
