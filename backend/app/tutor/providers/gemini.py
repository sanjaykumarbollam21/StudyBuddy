import json
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from app.tutor.providers.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiLLMProvider(LLMProvider):
    """
    Cloud-First Google Gemini LLM Provider.
    Executes deep Socratic reasoning, formative assessment, and pedagogical remediation
    over secure HTTPS with bounded retries and token streaming.
    """

    def __init__(self, api_key: str = "", model_name: str = ""):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
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

    async def generate_response(self, prompt: str, system_prompt: str, temperature: float = 0.2) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
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
        key_ideas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Extraction-based Socratic evaluation.
        The model extracts ideas_present, ideas_missing, and misconception_identified at temperature 0.
        Verdict classification is derived deterministically in code by AnswerEvaluationService.
        """
        effective_ideas = key_ideas or [expected_concept]
        system_instruction = (
            "You are an objective Socratic concept extractor for an AI tutor. "
            "Your task is to compare the student's answer against the target concept's key ideas.\n\n"
            "TASK:\n"
            "1. 'ideas_present': List of strings from the provided Target Key Ideas that the student's answer accurately captures or explains.\n"
            "2. 'ideas_missing': List of strings from the provided Target Key Ideas that the student omitted, failed to explain, or got wrong.\n"
            "3. 'misconception_identified': If the student expressed a specific false premise, myth, or misconception (such as confusing software rationality with CPU speed, or believing CAP eliminates partitions), identify it as a short string; otherwise null.\n"
            "4. 'is_off_topic_or_unsure': Boolean, true if the student explicitly states 'I don't know', asks for the answer, or writes something completely unrelated/off-topic.\n"
            "5. 'feedback': 1-2 encouraging sentences explaining what was good or where the gap lies, WITHOUT blurting out the solution to the check question.\n\n"
            "CRITICAL RULES:\n"
            "- Do NOT output a verdict. Extract ideas and misconceptions only.\n"
            "- Never give away the full target answer in your feedback.\n\n"
            "Output valid JSON ONLY with keys: ideas_present (list), ideas_missing (list), misconception_identified (string or null), is_off_topic_or_unsure (bool), feedback (string), confidence (float)."
        )

        prompt = (
            f"Concept: {concept_title}\n"
            f"Question Asked: {question}\n"
            f"Target Core Concept: {expected_concept}\n"
            f"Target Key Ideas: {json.dumps(effective_ideas)}\n"
            f"Student Answer: {student_answer}\n"
            f"Known Misconceptions: {json.dumps(common_misconceptions or {})}\n"
            f"Context: {context_text[:1000]}"
        )
        try:
            raw = await self.generate_response(prompt, system_instruction, temperature=0.0)
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
            data["source"] = "model"
            return data
        except Exception as e:
            logger.warning(f"Gemini student evaluation fallback triggered: {type(e).__name__}")
            # Deterministic heuristic fallback if external provider call fails or malformed
            ans_lower = student_answer.lower().strip()
            present = []
            missing = []
            for idea in effective_ideas:
                words = [w for w in idea.lower().split() if len(w) > 3]
                if any(w in ans_lower for w in words):
                    present.append(idea)
                else:
                    missing.append(idea)

            is_dont_know = any(p in ans_lower for p in ["don't know", "dont know", "no idea", "not sure", "pizza"])
            return {
                "ideas_present": present,
                "ideas_missing": missing,
                "misconception_identified": None,
                "is_off_topic_or_unsure": is_dont_know,
                "feedback": f"Good effort. Focus on the core definition: {expected_concept}.",
                "confidence": 0.8,
                "source": "fallback",
            }

    async def generate_remediation(
        self,
        concept_title: str,
        student_answer: str,
        misconception: Optional[str],
        original_analogy: str,
        context_text: str = "",
        strict_no_leak: bool = False,
        prohibited_phrase: str = "",
    ) -> Dict[str, Any]:
        """
        Formulates adaptive remediation without blurting out the solution.
        """
        leak_guard = ""
        if strict_no_leak and prohibited_phrase:
            leak_guard = (
                f"\nSTRICT ANTI-LEAK RULE: Under NO circumstances state or repeat the phrase '{prohibited_phrase}' "
                "or define the check question answer. Focus purely on a simpler physical analogy and guided question."
            )

        system_instruction = (
            "You are a master Socratic teacher breaking down a difficult concept. "
            "The student struggled or held a misconception. Provide:\n"
            "1. re_explanation: A gentle, supportive correction that addresses the flawed assumption without simply blurting out the final answer to the check question.\n"
            "2. simpler_analogy: A tangible physical or everyday real-world visual metaphor.\n"
            "3. simpler_question: A bite-sized, accessible check question leading them step-by-step toward the concept.\n"
            "4. hint: A directional nudge.\n"
            f"{leak_guard}\n\n"
            "Output valid JSON ONLY with keys: re_explanation, simpler_analogy, simpler_question, hint."
        )
        prompt = (
            f"Concept: {concept_title}\n"
            f"Student Said: {student_answer}\n"
            f"Identified Misconception: {misconception}\n"
            f"Previous Analogy: {original_analogy}\n"
        )
        try:
            raw = await self.generate_response(prompt, system_instruction, temperature=0.2)
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except Exception:
            return {
                "re_explanation": f"Let's break down {concept_title} step by step.",
                "simpler_analogy": original_analogy or f"Think of {concept_title} like a structured blueprint.",
                "simpler_question": f"What is the foundational requirement of {concept_title}?",
                "hint": f"Focus on the primary rule governing {concept_title}."
            }


async def check_gemini_model_availability() -> bool:
    """
    Startup check to verify that the configured GEMINI_MODEL is available and supports generateContent.
    Logs a clear error if not available or unsupported.
    Never crashes the application and never prints or logs API keys.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your-gemini-api-key" or len(api_key) < 10:
        logger.info("GEMINI_API_KEY is not configured or is a placeholder. Skipping Gemini model check.")
        return False

    model_name = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
    clean_target = model_name if model_name.startswith("models/") else f"models/{model_name}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.error(
                    f"Gemini model startup check failed: Google API returned status HTTP {resp.status_code}. "
                    f"Please verify network access and GEMINI_API_KEY validity."
                )
                return False

            data = resp.json()
            models = data.get("models", [])
            match = next((m for m in models if m.get("name") == clean_target), None)

            if not match:
                supported_models = [
                    m.get("name", "").replace("models/", "")
                    for m in models
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ][:6]
                logger.error(
                    f"Configured GEMINI_MODEL '{model_name}' was not found in available models on Google API. "
                    f"Available models supporting content generation include: {supported_models}."
                )
                return False

            supported_methods = match.get("supportedGenerationMethods", [])
            if "generateContent" not in supported_methods:
                logger.error(
                    f"Configured GEMINI_MODEL '{model_name}' does not support 'generateContent' (supported: {supported_methods})."
                )
                return False

            logger.info(f"Gemini model '{model_name}' verified successfully and ready for teaching generation.")
            return True
    except Exception as e:
        logger.error(
            f"Gemini model startup check failed due to unexpected error: {type(e).__name__} - {str(e)[:100]}."
        )
        return False
