from typing import Dict, Any, List, Optional
import re


class StudentIntent:
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    MISCONCEPTION = "misconception"
    WRONG = "wrong"
    AMBIGUOUS = "ambiguous"
    DONT_KNOW = "dont_know"
    REQUEST_HINT = "request_hint"
    REQUEST_SIMPLER = "request_simpler"
    REQUEST_WHY = "request_why"


class TeacherAction:
    ADVANCE_TOPIC = "advance_topic"
    PROMPT_MISSING_PIECE = "prompt_missing_piece"
    REMEDIATE_MISCONCEPTION = "remediate_misconception"
    REDIRECT_WITH_ANALOGY = "redirect_with_analogy"
    CLARIFY_AMBIGUITY = "clarify_ambiguity"
    GIVE_SCAFFOLDED_HINT = "give_scaffolded_hint"
    GIVE_CONCEPTUAL_CLUE = "give_conceptual_clue"
    EXPLAIN_WITH_ANALOGY = "explain_with_analogy"
    EXPLAIN_FIRST_PRINCIPLES = "explain_first_principles"


class PedagogicalEvaluator:
    """
    Phase 11: Pedagogical Evaluation Engine.
    Categorizes student responses across the full pedagogical spectrum
    and assigns deterministic pedagogical remediation actions.
    """

    MISCONCEPTION_PATTERNS = [
        (
            r"(prevention and avoidance are the same|prevention is the same as avoidance|prevention is avoidance)",
            "Deadlock prevention invalidates one of Coffman's conditions statically, while avoidance dynamically assesses state safety using algorithms like Banker's Algorithm.",
        ),
        (
            r"(mutex and semaphore are identical|mutex is just a counting semaphore|mutex is the same as counting semaphore)",
            "A mutex is a locking mechanism with ownership (only owner can unlock), whereas a counting semaphore is a signaling mechanism.",
        ),
        (
            r"(paging causes external fragmentation|paging has external fragmentation)",
            "Paging eliminates external fragmentation by using fixed-size frames, but it can suffer from internal fragmentation.",
        ),
    ]

    @classmethod
    def evaluate_response(
        cls,
        student_text: str,
        topic: str = "Deadlocks",
        key_concepts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        text = student_text.strip().lower()
        key_concepts = key_concepts or ["mutual exclusion", "hold and wait", "no preemption", "circular wait"]

        # 1. Meta-requests: Hint, Simpler, Why, Don't Know
        if re.search(r"\b(i don'?t know|no idea|not sure|dunno|have no clue)\b", text):
            return {
                "intent": StudentIntent.DONT_KNOW,
                "action": TeacherAction.GIVE_SCAFFOLDED_HINT,
                "feedback": f"That's completely fine! Think about {topic}: What needs to happen for two processes to be stuck waiting on each other?",
                "score": 0.0,
            }

        if re.search(r"\b(hint|give me a hint|clue|need a clue)\b", text):
            return {
                "intent": StudentIntent.REQUEST_HINT,
                "action": TeacherAction.GIVE_CONCEPTUAL_CLUE,
                "feedback": f"Here's a clue: Remember the 4 Coffman conditions for {topic}. What condition involves a cycle?",
                "score": 0.0,
            }

        if re.search(r"\b(simpler|simple words|plain english|eli5|explain simpler|like i'?m 5)\b", text):
            return {
                "intent": StudentIntent.REQUEST_SIMPLER,
                "action": TeacherAction.EXPLAIN_WITH_ANALOGY,
                "feedback": "Imagine a narrow bridge where two cars meet head-on. Neither can back up, and neither can move forward. That's a deadlock in everyday terms!",
                "score": 0.0,
            }

        if re.search(r"^(why|why\?|why is that\??|why so\??)$", text):
            return {
                "intent": StudentIntent.REQUEST_WHY,
                "action": TeacherAction.EXPLAIN_FIRST_PRINCIPLES,
                "feedback": "From first principles, when resources are non-shareable and processes cannot be preempted, circular dependencies make progress mathematically impossible without intervention.",
                "score": 0.0,
            }

        # 2. Check for Specific Misconceptions
        for pattern, explanation in cls.MISCONCEPTION_PATTERNS:
            if re.search(pattern, text):
                return {
                    "intent": StudentIntent.MISCONCEPTION,
                    "action": TeacherAction.REMEDIATE_MISCONCEPTION,
                    "feedback": f"Careful! That's a very common misconception. {explanation}",
                    "score": 0.25,
                }

        # 3. Check for Ambiguous / Vague Answers
        words = text.split()
        if len(words) <= 3 and not any(k in text for k in ["deadlock", "lock", "cycle", "wait", "process", "mutual"]):
            return {
                "intent": StudentIntent.AMBIGUOUS,
                "action": TeacherAction.CLARIFY_AMBIGUITY,
                "feedback": "You're touching on something, but could you be more specific? How does that relate to resource allocation?",
                "score": 0.3,
            }

        # 4. Check Key Concept Coverage
        matched_concepts = [c for c in key_concepts if c in text]

        if len(matched_concepts) >= 3 or ("circular wait" in text and ("hold and wait" in text or "mutual exclusion" in text)):
            return {
                "intent": StudentIntent.CORRECT,
                "action": TeacherAction.ADVANCE_TOPIC,
                "feedback": f"Spot on! You correctly identified the critical conditions ({', '.join(matched_concepts)}). Let's take it a step deeper.",
                "score": 1.0,
            }
        elif len(matched_concepts) >= 1 or any(w in text for w in ["circular", "waiting", "blocked", "resources", "processes"]):
            missing = [c for c in key_concepts if c not in matched_concepts]
            return {
                "intent": StudentIntent.PARTIALLY_CORRECT,
                "action": TeacherAction.PROMPT_MISSING_PIECE,
                "feedback": f"Great start! You mentioned relevant ideas, but what about conditions like {missing[0]}?",
                "score": 0.65,
            }
        else:
            return {
                "intent": StudentIntent.WRONG,
                "action": TeacherAction.REDIRECT_WITH_ANALOGY,
                "feedback": f"Not quite. Let's step back: in {topic}, processes are indefinitely blocked waiting for events that only other blocked processes can cause.",
                "score": 0.1,
            }
