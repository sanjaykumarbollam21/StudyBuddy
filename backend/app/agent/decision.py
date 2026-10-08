from typing import Dict, Any, List, Optional
import uuid


class ActionPermissionPolicy:
    SAFE_AUTOMATIC = {
        "generate_study_plan",
        "recalculate_plan",
        "create_practice_session",
        "schedule_revision",
        "generate_quiz",
        "update_mastery",
    }

    REQUIRES_PERMISSION = {
        "start_remediation_session",
        "change_exam_goal",
        "delete_material",
        "change_major_schedule",
        "use_cloud_ai",
        "share_data",
    }


class AgentDecisionEngine:
    """
    Phase 12: Autonomous Agent Decision Engine.
    Evaluates multi-factor student telemetry to select the highest-value
    learning action and allocates time across pedagogical engines.
    """

    DEFAULT_TOPIC_DATA = [
        {
            "topic": "Deadlocks & Synchronization",
            "mastery_percentage": 48.0,
            "exam_weight": 1.8,
            "misconception_count": 2,
            "prerequisites_satisfied": True,
            "weak_points": ["Prevention vs Avoidance", "Banker's Algorithm"],
        },
        {
            "topic": "Memory Management & Paging",
            "mastery_percentage": 68.0,
            "exam_weight": 1.4,
            "misconception_count": 0,
            "prerequisites_satisfied": True,
            "weak_points": ["Page Replacement Algorithms"],
        },
        {
            "topic": "CPU Scheduling Algorithms",
            "mastery_percentage": 85.0,
            "exam_weight": 1.0,
            "misconception_count": 0,
            "prerequisites_satisfied": True,
            "weak_points": [],
        },
    ]

    @classmethod
    def evaluate_highest_value_task(
        cls,
        available_minutes: int = 60,
        days_until_exam: int = 5,
        due_revision_count: int = 3,
        topic_telemetry: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        topics = topic_telemetry or cls.DEFAULT_TOPIC_DATA

        # Exam urgency factor: < 3 days -> 3.0, < 7 days -> 2.0, else 1.0
        if days_until_exam <= 3:
            exam_urgency = 3.0
        elif days_until_exam <= 7:
            exam_urgency = 2.0
        else:
            exam_urgency = 1.0

        # Score candidate topics
        scored_topics = []
        for t in topics:
            gap = max(0.0, (100.0 - t["mastery_percentage"]) / 100.0)
            exam_score = t["exam_weight"] * exam_urgency * 15.0
            gap_score = gap * 40.0
            misconception_score = min(30.0, t.get("misconception_count", 0) * 15.0)
            prereq_mult = 1.0 if t.get("prerequisites_satisfied", True) else 0.4

            priority_score = (gap_score + exam_score + misconception_score) * prereq_mult
            scored_topics.append({
                "topic": t["topic"],
                "score": round(priority_score, 2),
                "mastery_percentage": t["mastery_percentage"],
                "exam_weight": t["exam_weight"],
                "misconception_count": t.get("misconception_count", 0),
                "weak_points": t.get("weak_points", []),
            })

        # Select highest-value topic
        scored_topics.sort(key=lambda x: x["score"], reverse=True)
        top_topic = scored_topics[0]

        # Allocate available minutes across orchestrator engines
        actions = []
        if available_minutes >= 60:
            reteach_mins = 25
            practice_mins = 20
            revision_mins = min(15, due_revision_count * 5)
            # Adjust remainder
            reteach_mins += (available_minutes - (reteach_mins + practice_mins + revision_mins))

            actions = [
                {
                    "step": 1,
                    "type": "reteach",
                    "topic": top_topic["topic"],
                    "duration_mins": reteach_mins,
                    "engine": "TeacherEngine",
                    "description": f"Socratic reteaching focusing on {', '.join(top_topic['weak_points']) if top_topic['weak_points'] else top_topic['topic']}",
                },
                {
                    "step": 2,
                    "type": "practice",
                    "topic": top_topic["topic"],
                    "duration_mins": practice_mins,
                    "engine": "PracticeEngine",
                    "description": "5 targeted application and diagnostic questions",
                },
                {
                    "step": 3,
                    "type": "spaced_revision",
                    "topic": top_topic["topic"],
                    "duration_mins": revision_mins,
                    "engine": "RevisionEngine",
                    "description": f"Active recall review of {due_revision_count} overdue revision items",
                },
                {
                    "step": 4,
                    "type": "update_mastery",
                    "topic": top_topic["topic"],
                    "duration_mins": 0,
                    "engine": "MasteryEngine",
                    "description": "Recalculate multi-factor mastery and re-sequence planner timeline",
                },
            ]
        elif available_minutes >= 30:
            reteach_mins = 18
            practice_mins = 12
            actions = [
                {
                    "step": 1,
                    "type": "reteach",
                    "topic": top_topic["topic"],
                    "duration_mins": reteach_mins,
                    "engine": "TeacherEngine",
                    "description": f"High-yield breakdown of {top_topic['topic']}",
                },
                {
                    "step": 2,
                    "type": "practice",
                    "topic": top_topic["topic"],
                    "duration_mins": practice_mins,
                    "engine": "PracticeEngine",
                    "description": "Targeted active recall practice questions",
                },
                {
                    "step": 3,
                    "type": "update_mastery",
                    "topic": top_topic["topic"],
                    "duration_mins": 0,
                    "engine": "MasteryEngine",
                    "description": "Dynamic mastery calibration",
                },
            ]
        else:
            # 15 mins micro-session
            actions = [
                {
                    "step": 1,
                    "type": "spaced_revision",
                    "topic": top_topic["topic"],
                    "duration_mins": available_minutes,
                    "engine": "RevisionEngine",
                    "description": "Rapid active recall flash questions",
                },
            ]

        # Determine safety permission level
        permission_level = "requires_permission"  # Multi-step remediation requires student confirmation

        reason = (
            f"Exam is {days_until_exam} days away. {top_topic['topic']} is at {top_topic['mastery_percentage']}% mastery "
            f"(exam weight: {top_topic['exam_weight']}x) with {top_topic['misconception_count']} unresolved misconceptions."
        )

        return {
            "goal": f"Repair {top_topic['topic']} knowledge gap & misconceptions",
            "reason": reason,
            "priority": "critical" if top_topic["mastery_percentage"] < 50.0 else "high",
            "permission_level": permission_level,
            "allocated_minutes": available_minutes,
            "proposed_actions": actions,
            "explanation_breakdown": {
                "top_topic": top_topic["topic"],
                "mastery_percentage": top_topic["mastery_percentage"],
                "priority_score": top_topic["score"],
                "exam_weight": top_topic["exam_weight"],
                "days_until_exam": days_until_exam,
                "due_revisions": due_revision_count,
                "all_scored_topics": scored_topics,
                "rationale": f"Topic '{top_topic['topic']}' holds highest urgency score ({top_topic['score']}) due to weak mastery and upcoming exam deadline.",
            },
        }

    @classmethod
    def evaluate_competitive_intent(
        cls,
        user_prompt: str,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Parses competitive exam natural language queries and returns actionable
        agent intent, recommended engine, and parameters.
        """
        prompt_lower = user_prompt.lower().strip()
        exam_code = (user_profile or {}).get("exam_code", "upsc_cse")

        if any(kw in prompt_lower for kw in ["what should i study", "what to study", "recommend", "next topic"]):
            return {
                "intent": "study_recommendation",
                "engine": "StudyPlannerEngine",
                "action": "recommend_next_slot",
                "exam_code": exam_code,
                "response": "Based on your current mastery and PYQ weightage, here is your prioritized study task.",
                "suggested_slot": "static_core",
            }
        elif any(kw in prompt_lower for kw in ["current affair", "news", "today's editorial", "newspaper"]):
            return {
                "intent": "current_affairs",
                "engine": "CurrentAffairsService",
                "action": "fetch_or_quiz",
                "exam_code": exam_code,
                "response": "Here are today's high-yield current affairs linked to static syllabus concepts.",
            }
        elif any(kw in prompt_lower for kw in ["mains answer", "evaluate answer", "answer writing", "evaluate my answer"]):
            return {
                "intent": "mains_answer_evaluation",
                "engine": "AnswerWritingService",
                "action": "evaluate_submission",
                "exam_code": exam_code,
                "response": "Ready for Mains answer evaluation across all 8 dimensions.",
            }
        elif any(kw in prompt_lower for kw in ["csat", "aptitude", "comprehension", "paper 2"]):
            return {
                "intent": "csat_practice",
                "engine": "CSATEngine",
                "action": "start_timed_session",
                "exam_code": exam_code,
                "response": "Starting a timed CSAT practice drill with negative marking penalties.",
            }
        elif any(kw in prompt_lower for kw in ["pyq", "previous year", "past question"]):
            return {
                "intent": "pyq_practice",
                "engine": "PYQService",
                "action": "filter_pyqs",
                "exam_code": exam_code,
                "response": "Filtering high-yield previous year questions for your selected topics.",
            }
        elif any(kw in prompt_lower for kw in ["readiness", "score", "how prepared", "readiness index", "dashboard"]):
            return {
                "intent": "readiness_check",
                "engine": "ReadinessDashboardService",
                "action": "compute_readiness_index",
                "exam_code": exam_code,
                "response": "Synthesizing your multi-dimensional examination readiness report.",
            }
        else:
            return {
                "intent": "socratic_tutoring",
                "engine": "TeacherEngine",
                "action": "socratic_query",
                "exam_code": exam_code,
                "response": "Analyzing your conceptual query within your competitive exam syllabus.",
            }
