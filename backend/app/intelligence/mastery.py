from typing import List, Dict, Any, Optional
import math
from datetime import datetime, timezone


def calculate_advanced_mastery(
    recent_accuracy: float,
    historical_accuracy: float,
    practice_count: int,
    avg_difficulty: float = 1.0,  # 0.5 (easy), 1.0 (medium), 1.5 (hard)
    question_type: str = "conceptual",  # conceptual, coding, applied, recall
    mistake_recurrence_count: int = 0,
    misconceptions_detected: int = 0,
    days_since_last_recall: float = 0.0,
    prerequisite_mastery: Optional[float] = None,
    student_confidence: float = 0.7,  # 0.0 to 1.0
    exam_weight: float = 1.0,  # relative weight 1.0 - 2.0
) -> Dict[str, Any]:
    """
    Phase 10.5: Multi-factor learning intelligence mastery calculation.
    Incorporates:
    - Recent performance (30%)
    - Historical performance (15%)
    - Difficulty factor (15%)
    - Question type complexity (10%)
    - Mistake & misconception penalties (up to -20%)
    - Recall interval decay (Ebbinghaus curve adjustment)
    - Prerequisite mastery gate
    - Student confidence alignment
    """
    # 1. Base accuracy weighted by recency
    # If few practices, weight recent more heavily
    recent_weight = 0.35 if practice_count < 5 else 0.25
    hist_weight = 0.15 if practice_count < 5 else 0.20
    base_score = (recent_accuracy * recent_weight) + (historical_accuracy * hist_weight)

    # 2. Difficulty multiplier (harder questions reward more mastery if answered well)
    # difficulty normalized around 1.0 (range 0.5 - 1.5)
    diff_clamped = max(0.5, min(1.5, avg_difficulty))
    difficulty_score = (recent_accuracy * (diff_clamped / 1.5)) * 0.15

    # 3. Question type complexity weight
    type_factors = {
        "recall": 0.8,
        "conceptual": 1.0,
        "applied": 1.15,
        "coding": 1.25,
    }
    type_mult = type_factors.get(question_type.lower(), 1.0)
    question_type_score = (recent_accuracy * (type_mult / 1.25)) * 0.10

    # 4. Student confidence bonus/alignment (reward high performance with high confidence, penalize guessing)
    # If high accuracy + high confidence: +0.05
    # If low accuracy + high confidence (overconfidence): -0.05
    confidence_delta = 0.0
    if recent_accuracy >= 0.7:
        confidence_delta = 0.05 * student_confidence
    else:
        # Overconfidence penalty: confident but wrong
        if student_confidence > 0.6:
            confidence_delta = -0.05 * student_confidence

    # 5. Penalties for repeated mistakes & misconceptions
    mistake_penalty = min(0.15, mistake_recurrence_count * 0.03)
    misconception_penalty = min(0.15, misconceptions_detected * 0.05)
    penalties = mistake_penalty + misconception_penalty

    # 6. Forgetting curve / Recall interval decay
    # R = e^(-t / S), where S is memory strength approximated by practice count
    stability = max(1.0, float(practice_count) * 2.5)
    retention_factor = math.exp(-days_since_last_recall / stability)
    # Retention affects memory component
    retention_adjustment = (retention_factor - 1.0) * 0.15

    # Sum raw mastery before gating
    raw_score = (
        base_score
        + difficulty_score
        + question_type_score
        + confidence_delta
        - penalties
        + retention_adjustment
    )

    # Normalize to 0.0 - 1.0 scale
    normalized_mastery = max(0.0, min(1.0, raw_score / 0.70))

    # 7. Prerequisite gating (if prerequisite is weak (<0.5), cap maximum mastery at 0.75)
    gated_reason = None
    if prerequisite_mastery is not None and prerequisite_mastery < 0.50:
        if normalized_mastery > 0.75:
            normalized_mastery = 0.75
            gated_reason = "Capped due to weak prerequisite mastery (< 50%)"

    percentage = round(normalized_mastery * 100.0, 1)

    return {
        "mastery_percentage": percentage,
        "normalized_score": round(normalized_mastery, 4),
        "retention_factor": round(retention_factor, 3),
        "mistake_penalty": round(mistake_penalty, 3),
        "misconception_penalty": round(misconception_penalty, 3),
        "is_mastered": percentage >= 80.0,
        "gated_reason": gated_reason,
        "exam_weight": exam_weight,
    }


def calculate_topic_urgency_score(
    mastery_percentage: float,
    exam_weight: float,
    days_until_exam: int,
    days_since_revision: float,
    is_prerequisite_satisfied: bool = True,
    learning_speed_factor: float = 1.0,  # 0.8 = slower, 1.2 = fast
) -> float:
    """
    Intelligent Planner Optimization function (Phase 10.5).
    Computes priority score (0.0 to 100.0+) for scheduling study items.
    """
    # 1. Mastery gap (0 to 1.0)
    gap = max(0.0, (100.0 - mastery_percentage) / 100.0)

    # 2. Exam proximity multiplier: 1 day away is urgent, 30 days is less urgent
    exam_factor = max(1.0, 30.0 / max(1, days_until_exam))

    # 3. Revision urgency from forgetting
    revision_urgency = min(2.0, days_since_revision / 3.0)

    # 4. Prerequisite readiness multiplier (unblocked topics get prioritized)
    prereq_mult = 1.0 if is_prerequisite_satisfied else 0.4

    # 5. Speed adjustment (students who take longer to learn need earlier scheduling)
    speed_urgency = 1.2 / max(0.5, learning_speed_factor)

    raw_urgency = (
        (gap * 40.0)
        + (exam_weight * exam_factor * 15.0)
        + (revision_urgency * 20.0)
    ) * prereq_mult * (speed_urgency / 1.2)

    return round(raw_urgency, 2)
