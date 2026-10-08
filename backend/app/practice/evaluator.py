import re
from typing import Optional, Set
from app.practice.types import QuestionType, EvaluationVerdict, PracticeEvaluation, GeneratedQuestion
from app.tutor.providers import LLMProvider


class AnswerEvaluator:
    """
    Evaluates student answers across all 7 question types with partial-credit scoring,
    distractor misconception identification, and pedagogical remediation guidance.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider

    async def evaluate(
        self,
        question: GeneratedQuestion,
        student_response: str,
    ) -> PracticeEvaluation:
        q_type = question.question_type
        clean_resp = student_response.strip()

        if q_type == QuestionType.MCQ or q_type == QuestionType.TRUE_FALSE:
            return self._evaluate_mcq(question, clean_resp)

        if q_type == QuestionType.MULTIPLE_SELECT:
            return self._evaluate_multiple_select(question, clean_resp)

        if q_type == QuestionType.FILL_BLANK or q_type == QuestionType.SHORT_ANSWER:
            return self._evaluate_short_or_fill(question, clean_resp)

        if q_type == QuestionType.SCENARIO:
            return self._evaluate_scenario(question, clean_resp)

        if q_type == QuestionType.CODING:
            return self._evaluate_coding(question, clean_resp)

        # Default fallback
        return self._evaluate_short_or_fill(question, clean_resp)

    def _evaluate_mcq(self, question: GeneratedQuestion, response: str) -> PracticeEvaluation:
        correct = question.correct_answer.strip().lower()
        student = response.strip().lower()

        # Check for direct or letter match (e.g., 'A', 'B', or full text)
        is_exact = student == correct or (len(student) > 3 and student in correct) or (len(correct) > 3 and correct in student)

        if is_exact:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.CORRECT,
                is_correct=True,
                score=1.0,
                feedback="Correct! Excellent conceptual grasp.",
                explanation=question.explanation,
                concept_tag=question.concept_tag,
            )

        # Diagnose distractor misconception
        misconception = None
        for option, explanation in question.distractor_explanations.items():
            opt_clean = option.lower().strip()
            if opt_clean in student or student in opt_clean:
                misconception = f"Misconception regarding '{option}': {explanation}"
                break

        if not misconception:
            misconception = f"Your choice '{response}' does not satisfy the requirements of {question.concept_tag or 'this concept'}."

        remediation = (
            f"Review the core distinction: {question.explanation}. "
            f"You may want to ask Study Buddy's AI Teacher to re-explain {question.concept_tag or 'this topic'}."
        )

        return PracticeEvaluation(
            verdict=EvaluationVerdict.INCORRECT,
            is_correct=False,
            score=0.0,
            feedback=f"Incorrect. {misconception}",
            explanation=question.explanation,
            misconception_identified=misconception,
            remediation_advice=remediation,
            concept_tag=question.concept_tag,
        )

    def _evaluate_multiple_select(self, question: GeneratedQuestion, response: str) -> PracticeEvaluation:
        # Expected comma-separated or list of correct items
        expected_items = [item.strip().lower() for item in question.correct_answer.split(",") if item.strip()]
        # Student responses can be comma-separated or newline-separated
        student_items = [item.strip().lower() for item in re.split(r"[,;\n]+", response) if item.strip()]

        expected_set = set(expected_items)
        student_set = set(student_items)

        correct_selected = expected_set.intersection(student_set)
        incorrect_selected = student_set.difference(expected_set)

        if expected_set == student_set:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.CORRECT,
                is_correct=True,
                score=1.0,
                feedback="Spot on! You selected all correct options and avoided every distractor.",
                explanation=question.explanation,
                concept_tag=question.concept_tag,
            )

        # Partial credit calculation
        precision = len(correct_selected) / len(student_set) if student_set else 0.0
        recall = len(correct_selected) / len(expected_set) if expected_set else 0.0
        score = round((precision + recall) / 2, 2)

        if score > 0.3:
            verdict = EvaluationVerdict.PARTIALLY_CORRECT
            feedback = (
                f"Partially correct (Score: {int(score * 100)}%). You correctly identified: "
                f"{', '.join(correct_selected)}. "
            )
            if incorrect_selected:
                feedback += f"However, you incorrectly included: {', '.join(incorrect_selected)}."
        else:
            verdict = EvaluationVerdict.INCORRECT
            score = 0.0
            feedback = "Incorrect selection."

        misconception = None
        for inc in incorrect_selected:
            for opt, explanation in question.distractor_explanations.items():
                if opt.lower() in inc or inc in opt.lower():
                    misconception = f"Misconception on '{opt}': {explanation}"
                    break

        return PracticeEvaluation(
            verdict=verdict,
            is_correct=verdict == EvaluationVerdict.CORRECT,
            score=score,
            feedback=feedback,
            explanation=question.explanation,
            misconception_identified=misconception,
            remediation_advice=f"Check all requirements: {question.explanation}",
            concept_tag=question.concept_tag,
        )

    def _evaluate_short_or_fill(self, question: GeneratedQuestion, response: str) -> PracticeEvaluation:
        clean_resp = re.sub(r"[^\w\s]", "", response.lower()).strip()
        clean_correct = re.sub(r"[^\w\s]", "", question.correct_answer.lower()).strip()

        # Exact or near-exact match
        if clean_resp == clean_correct:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.CORRECT,
                is_correct=True,
                score=1.0,
                feedback="Correct! Precise answer.",
                explanation=question.explanation,
                concept_tag=question.concept_tag,
            )

        # Keyword checking for partial credit
        correct_words = set(clean_correct.split())
        resp_words = set(clean_resp.split())
        overlap = correct_words.intersection(resp_words)

        if len(overlap) >= len(correct_words) * 0.7 and len(resp_words) > 0:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.CORRECT,
                is_correct=True,
                score=1.0,
                feedback=f"Correct! Your answer captured the key concept: '{question.correct_answer}'.",
                explanation=question.explanation,
                concept_tag=question.concept_tag,
            )

        if len(overlap) >= 1 and len(correct_words) > 1:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.PARTIALLY_CORRECT,
                is_correct=False,
                score=0.5,
                feedback=f"Partially correct. You mentioned '{list(overlap)[0]}', but the expected term is '{question.correct_answer}'.",
                explanation=question.explanation,
                misconception_identified=f"Incomplete terminology. Expected '{question.correct_answer}'.",
                remediation_advice=f"Review the exact definition: {question.explanation}",
                concept_tag=question.concept_tag,
            )

        return PracticeEvaluation(
            verdict=EvaluationVerdict.INCORRECT,
            is_correct=False,
            score=0.0,
            feedback=f"Incorrect. The expected answer is '{question.correct_answer}'.",
            explanation=question.explanation,
            misconception_identified=f"Did not recognize key concept: {question.correct_answer}",
            remediation_advice=f"Review: {question.explanation}",
            concept_tag=question.concept_tag,
        )

    def _evaluate_scenario(self, question: GeneratedQuestion, response: str) -> PracticeEvaluation:
        clean_resp = response.lower()
        key_phrases = [k.strip().lower() for k in re.split(r"[.;,]+", question.correct_answer) if len(k.strip()) > 3]

        matched = 0
        for phrase in key_phrases:
            words = phrase.split()
            if any(w in clean_resp for w in words if len(w) > 3):
                matched += 1

        ratio = matched / len(key_phrases) if key_phrases else 0.0

        if ratio >= 0.7:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.CORRECT,
                is_correct=True,
                score=1.0,
                feedback="Excellent scenario diagnosis and proposal!",
                explanation=question.explanation,
                concept_tag=question.concept_tag,
            )
        elif ratio >= 0.35:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.PARTIALLY_CORRECT,
                is_correct=False,
                score=0.6,
                feedback="Good diagnosis, but incomplete remediation proposal.",
                explanation=question.explanation,
                misconception_identified="Partial scenario resolution.",
                remediation_advice=f"Complete solution: {question.explanation}",
                concept_tag=question.concept_tag,
            )
        else:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.INCORRECT,
                is_correct=False,
                score=0.0,
                feedback="Incorrect analysis of the scenario.",
                explanation=question.explanation,
                misconception_identified="Incomplete scenario problem identification.",
                remediation_advice=question.explanation,
                concept_tag=question.concept_tag,
            )

    def _evaluate_coding(self, question: GeneratedQuestion, response: str) -> PracticeEvaluation:
        # Check required syntactic invariants
        clean_code = response.lower()
        has_class_def = "class" in clean_code or "def" in clean_code
        has_lock_or_cond = "condition" in clean_code or "wait" in clean_code or "acquire" in clean_code or "lock" in clean_code
        has_signal = "notify" in clean_code or "signal" in clean_code or "release" in clean_code

        score = 0.0
        if has_class_def:
            score += 0.3
        if has_lock_or_cond:
            score += 0.4
        if has_signal:
            score += 0.3

        if score >= 0.9:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.CORRECT,
                is_correct=True,
                score=1.0,
                feedback="Clean and correct implementation!",
                explanation=question.explanation,
                concept_tag=question.concept_tag,
            )
        elif score >= 0.5:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.PARTIALLY_CORRECT,
                is_correct=False,
                score=score,
                feedback="Implementation is partially complete but missing concurrency coordination primitives.",
                explanation=question.explanation,
                misconception_identified="Concurrency synchronization missing wait/notify or lock invariants.",
                remediation_advice=question.explanation,
                concept_tag=question.concept_tag,
            )
        else:
            return PracticeEvaluation(
                verdict=EvaluationVerdict.INCORRECT,
                is_correct=False,
                score=0.0,
                feedback="Implementation does not meet the specified requirements.",
                explanation=question.explanation,
                misconception_identified="Failed to implement required thread safety mechanisms.",
                remediation_advice=question.explanation,
                concept_tag=question.concept_tag,
            )
