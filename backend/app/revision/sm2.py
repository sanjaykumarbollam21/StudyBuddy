import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SM2Scheduler:
    """
    Enhanced SuperMemo SM-2 Spaced Repetition Algorithm.
    Calculates repetition intervals, ease factor adaptation, and
    multi-factor retention decay.
    """

    MIN_EASE_FACTOR: float = 1.3
    DEFAULT_EASE_FACTOR: float = 2.5

    @classmethod
    def calculate_sm2(
        cls,
        quality: int,  # 0 to 5 rating
        repetition_count: int,
        interval_days: int,
        ease_factor: float,
    ) -> Dict[str, Any]:
        """
        Calculates updated repetition count, interval (days), next review timestamp,
        and adjusted ease factor.
        """
        # Clamp quality to 0-5
        q = max(0, min(5, quality))
        ef = max(cls.MIN_EASE_FACTOR, ease_factor or cls.DEFAULT_EASE_FACTOR)

        # 1. Update Ease Factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        delta_ef = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        new_ef = max(cls.MIN_EASE_FACTOR, round(ef + delta_ef, 2))

        # 2. Determine repetition interval
        if q < 3:
            # Failed recall: reset repetition count, schedule for tomorrow (or immediate review)
            new_repetition_count = 0
            new_interval_days = 1
        else:
            # Successful recall
            if repetition_count == 0:
                new_interval_days = 1
                new_repetition_count = 1
            elif repetition_count == 1:
                new_interval_days = 6
                new_repetition_count = 2
            else:
                new_interval_days = max(1, round(interval_days * new_ef))
                new_repetition_count = repetition_count + 1

        next_review_date = utc_now() + timedelta(days=new_interval_days)

        return {
            "repetition_count": new_repetition_count,
            "interval_days": new_interval_days,
            "ease_factor": new_ef,
            "next_review_date": next_review_date,
            "is_passed": q >= 3,
        }

    @classmethod
    def calculate_hardened_mastery(
        cls,
        current_mastery: float,
        quality_history: List[int],
        latest_quality: int,
        days_since_last_recall: int,
        difficulty_weight: float = 1.0,
        misconception_count: int = 0,
        consecutive_successes: int = 0,
    ) -> float:
        """
        Hardened multi-factor mastery calculation requested by pedagogical design:
        - Incorporates historical recall trajectory (trend direction),
        - Memory retention decay based on days elapsed beyond schedule,
        - Repeated misconception penalties,
        - Question difficulty weighting,
        - Consecutive independent recall boosts.
        """
        # Base score from latest quality (0-5 mapped to 0-100)
        quality_score = (latest_quality / 5.0) * 100.0

        # Trajectory multiplier: reward upward momentum, penalize downward regression
        trajectory_bonus = 0.0
        if len(quality_history) >= 2:
            prev_recent = quality_history[-2:]
            if prev_recent[-1] > prev_recent[-2]:
                trajectory_bonus += 5.0  # Upward progress
            elif prev_recent[-1] < prev_recent[-2]:
                trajectory_bonus -= 8.0  # Regression penalty

        # Memory retention decay (Ebbinghaus forgetting curve factor)
        # Decay is gentle for first few days, accelerates if overdue beyond 7 days
        decay_factor = 1.0
        if days_since_last_recall > 3:
            overdue_days = days_since_last_recall - 3
            decay_factor = max(0.65, math.exp(-0.03 * overdue_days))

        # Repeated misconception penalty (up to -20%)
        misconception_penalty = min(20.0, misconception_count * 5.0)

        # Consistency boost for multiple independent successful recalls
        consistency_boost = min(15.0, consecutive_successes * 2.5)

        # Weighted calculation combining damped historical score and new evidence
        weighted_current = (current_mastery * decay_factor) * 0.55
        weighted_new = (quality_score * difficulty_weight) * 0.45

        calculated = weighted_current + weighted_new + trajectory_bonus + consistency_boost - misconception_penalty
        return round(max(5.0, min(100.0, calculated)), 1)
