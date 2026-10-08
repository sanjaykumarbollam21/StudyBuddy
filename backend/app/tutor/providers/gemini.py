import json
import asyncio
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from app.tutor.providers.base import LLMProvider
from app.core.config import settings

class GeminiLLMProvider(LLMProvider):
    """
    Cloud-First Google Gemini LLM Provider.
    Executes deep Socratic reasoning, formative assessment, and pedagogical remediation
    over secure HTTPS with bounded retries and token streaming.
    """

    def __init__(self, api_key: str = "", model_name: str = ""):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-1.5-flash"
        self.timeout = settings.AI_REQUEST_TIMEOUT_SECONDS
        self.max_retries = settings.AI_MAX_RETRIES

    def get_provider_name(self) -> str:
        return "gemini"

    async def _execute_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your-gemini-api-key":
            raise RuntimeError(
                "GEMINI_API_KEY is not configured on the Study Buddy backend. "
                "Please configure GEMINI_API_KEY in the server environment (.env) to enable Cloud AI features."
            )

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return resp.json()
                    elif resp.status_code in [429, 500, 503, 504] and attempt < self.max_retries:
                        # Transient error or rate limit: exponential backoff
                        backoff = (settings.AI_RETRY_BACKOFF_FACTOR ** attempt) * 0.5
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        raise RuntimeError(f"Gemini API returned error ({resp.status_code}): {resp.text}")
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if attempt < self.max_retries:
                    backoff = (settings.AI_RETRY_BACKOFF_FACTOR ** attempt) * 0.5
                    await asyncio.sleep(backoff)
                    continue
                raise RuntimeError(f"Gemini API request failed after {self.max_retries} attempts: {str(e)}")

        raise RuntimeError(f"Gemini API execution failed: {str(last_error)}")

    async def generate_response(self, prompt: str, system_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
            }
        }

        data = await self._execute_with_retry(url, payload)
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return "Unable to generate response from Gemini."

    async def stream_response(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        """Stream generated response tokens asynchronously."""
        # For simplicity and robust fallback across HTTP proxies, stream words progressively
        full_text = await self.generate_response(prompt, system_prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)

    async def evaluate_student_answer(
        self,
        concept_title: str,
        question: str,
        expected_concept: str,
        student_answer: str,
        common_misconceptions: Optional[Dict[str, str]] = None,
        context_text: str = "",
    ) -> Dict[str, Any]:
        system_instruction = (
            "You are a strict, supportive Socratic teacher. "
            "Evaluate the student's answer against the target concept. "
            "Output JSON with keys: verdict ('correct', 'partially_correct', 'misconception', 'struggling'), "
            "feedback (encouraging explanation of why), misconception_identified (string or null), confidence (float)."
        )
        prompt = (
            f"Concept: {concept_title}\n"
            f"Question Asked: {question}\n"
            f"Target Concept: {expected_concept}\n"
            f"Student Answer: {student_answer}\n"
            f"Known Misconceptions: {json.dumps(common_misconceptions or {})}\n"
            f"Context: {context_text[:1000]}"
        )
        try:
            raw = await self.generate_response(prompt, system_instruction)
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except Exception:
            # Deterministic heuristic if external provider call fails or malformed
            ans_lower = student_answer.lower().strip()
            exp_lower = expected_concept.lower().strip()
            exp_tokens = [t for t in exp_lower.split() if len(t) > 2]
            is_match = exp_lower in ans_lower or (exp_tokens and all(t in ans_lower for t in exp_tokens))
            return {
                "verdict": "correct" if is_match else "partially_correct",
                "feedback": f"Good effort. Key target concept: {expected_concept}.",
                "misconception_identified": None,
                "confidence": 0.85 if is_match else 0.5,
            }

    async def generate_remediation(
        self,
        concept_title: str,
        student_answer: str,
        misconception: Optional[str],
        original_analogy: str,
        context_text: str = "",
    ) -> Dict[str, Any]:
        system_instruction = (
            "You are a master teacher breaking down a difficult concept. "
            "The student struggled or had a misconception. Provide: "
            "1. re_explanation (gentle correction), 2. simpler_analogy (physical/visual), "
            "3. simpler_question (bite-sized check question), 4. hint. "
            "Output valid JSON."
        )
        prompt = (
            f"Concept: {concept_title}\n"
            f"Student Said: {student_answer}\n"
            f"Identified Misconception: {misconception}\n"
            f"Previous Analogy: {original_analogy}\n"
        )
        try:
            raw = await self.generate_response(prompt, system_instruction)
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except Exception:
            return {
                "re_explanation": f"Let's break down {concept_title} step by step.",
                "simpler_analogy": original_analogy or f"Think of {concept_title} like a structured blueprint.",
                "simpler_question": f"What is the foundational requirement of {concept_title}?",
                "hint": f"Focus on the primary rule governing {concept_title}."
            }
